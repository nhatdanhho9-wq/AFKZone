import 'dart:async';
import 'dart:convert';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'remote_service.dart';

/// WebRTC Service for Remote Preview v0.1
/// Handles: PeerConnection, signaling WebSocket, SDP/ICE
class WebRTCService {
  RTCPeerConnection? _peerConnection;
  WebSocketChannel? _wsChannel;
  MediaStream? _localStream;
  MediaStream? _remoteStream;
  
  final String sessionId;
  final bool isHost;
  
  // Callbacks
  Function(MediaStream)? onRemoteStream;
  Function(RTCPeerConnectionState)? onConnectionState;
  Function(String)? onError;
  
  // 2-step host_ready callbacks
  Function(String requestId)? onEnableScreenCapture; // Host receives: show MediaProjection
  Function()? onWaitHostReady; // Controller receives: show waiting UI
  Function(String sessionId, String controllerToken)? onHostReady; // Controller receives: auto-continue SDP
  
  WebRTCService({
    required this.sessionId,
    required this.isHost,
  });

  /// Initialize WebRTC with TURN credentials
  Future<bool> initialize() async {
    try {
      // Get TURN credentials
      final turnCreds = await RemoteService.getTurnCredentials(sessionId);
      if (turnCreds == null) {
        onError?.call('Failed to get TURN credentials');
        return false;
      }

      // ICE servers configuration
      final config = {
        'iceServers': [
          {
            'urls': turnCreds.urls,
            'username': turnCreds.username,
            'credential': turnCreds.credential,
          },
          // Fallback STUN
          {'urls': 'stun:stun.l.google.com:19302'},
        ],
        'iceTransportPolicy': 'relay', // Force TURN relay
      };

      // Create peer connection
      _peerConnection = await createPeerConnection(config);
      
      // Set up event handlers
      _peerConnection!.onIceCandidate = _onIceCandidate;
      _peerConnection!.onTrack = _onTrack;
      _peerConnection!.onConnectionState = (state) {
        print('[WebRTC] Connection state: $state');
        onConnectionState?.call(state);
      };

      print('[WebRTC] Initialized with TURN: ${turnCreds.urls}');
      return true;
    } catch (e) {
      print('[WebRTC] Initialize error: $e');
      onError?.call(e.toString());
      return false;
    }
  }

  /// Connect to signaling WebSocket
  Future<bool> connectSignaling({required String wsToken}) async {
    try {
      final wsUrl = RemoteService.signalingUrl(sessionId: sessionId, wsToken: wsToken);

      _wsChannel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      _wsChannel!.stream.listen(
        (message) => _handleSignalingMessage(message),
        onError: (e) {
          print('[WebRTC] WS error: $e');
          onError?.call('Signaling error: $e');
        },
        onDone: () {
          print('[WebRTC] WS closed');
        },
      );

      print('[WebRTC] Connected to signaling: $wsUrl');
      return true;
    } catch (e) {
      print('[WebRTC] Connect signaling error: $e');
      onError?.call(e.toString());
      return false;
    }
  }

  /// Start as viewer (receive remote stream)
  Future<void> startViewer() async {
    if (_peerConnection == null) return;

    // Add transceiver for receiving video
    await _peerConnection!.addTransceiver(
      kind: RTCRtpMediaType.RTCRtpMediaTypeVideo,
      init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
    );
    await _peerConnection!.addTransceiver(
      kind: RTCRtpMediaType.RTCRtpMediaTypeAudio,
      init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
    );

    // Create offer
    final offer = await _peerConnection!.createOffer();
    await _peerConnection!.setLocalDescription(offer);
    
    // Send offer via signaling
    _sendSignaling({
      'type': 'sdp_offer',
      'payload': {'sdp': offer.sdp},
    });

    print('[WebRTC] Viewer started, offer sent');
  }

  /// Start as host (send screen capture)
  Future<void> startHost(MediaStream screenStream) async {
    if (_peerConnection == null) return;

    _localStream = screenStream;
    
    // Add screen capture tracks
    for (final track in screenStream.getTracks()) {
      await _peerConnection!.addTrack(track, screenStream);
    }

    print('[WebRTC] Host started, waiting for offer');
  }

  /// Handle incoming signaling message
  void _handleSignalingMessage(dynamic message) async {
    try {
      print('[WebRTC] <<< RAW WS MESSAGE: $message');
      final data = json.decode(message);
      final type = data['type'];
      print('[WebRTC] <<< Parsed type=$type, full data=$data');
      final payload = (data['payload'] is Map<String, dynamic>)
          ? (data['payload'] as Map<String, dynamic>)
          : <String, dynamic>{};

      switch (type) {
        case 'sdp_offer':
          await _handleOffer(payload['sdp']?.toString() ?? '');
          break;
        case 'sdp_answer':
          await _handleAnswer(payload['sdp']?.toString() ?? '');
          break;
        case 'ice_candidate':
          await _handleIceCandidate(payload);
          break;
        case 'control_ready':
          print('[WebRTC] Control ready');
          break;
        // 2-step host_ready flow
        case 'enable_screen_capture':
          // Host receives: show MediaProjection prompt
          // Try multiple field names for request_id
          final requestId = payload['request_id']?.toString() ?? 
                           data['request_id']?.toString() ?? 
                           '';
          print('[WebRTC] >>> HOST: enable_screen_capture, request_id=$requestId, payload=$payload');
          onEnableScreenCapture?.call(requestId);
          break;
        case 'wait_host_ready':
          // Controller receives: show waiting UI, DO NOT SDP yet
          print('[WebRTC] Controller: wait_host_ready');
          onWaitHostReady?.call();
          break;
        case 'host_ready':
          // Controller receives: auto-continue SDP with session_id + controller_token
          final sid = payload['session_id']?.toString() ?? '';
          final ctoken = payload['controller_token']?.toString() ?? '';
          print('[WebRTC] Controller: host_ready, session_id=$sid');
          onHostReady?.call(sid, ctoken);
          break;
        case 'remote_cancelled':
        case 'remote_rejected':
          print('[WebRTC] Remote session cancelled/rejected');
          // Signal close
          onConnectionState?.call(RTCPeerConnectionState.RTCPeerConnectionStateClosed);
          break;
        case 'error':
          onError?.call(payload['message']?.toString() ?? 'Unknown error');
          break;
      }
    } catch (e) {
      print('[WebRTC] Handle message error: $e');
    }
  }

  /// Handle SDP offer (host receives from viewer)
  Future<void> _handleOffer(String sdp) async {
    if (_peerConnection == null) return;
    if (sdp.isEmpty) {
      onError?.call('Received empty SDP offer');
      return;
    }

    await _peerConnection!.setRemoteDescription(
      RTCSessionDescription(sdp, 'offer'),
    );

    final answer = await _peerConnection!.createAnswer();
    await _peerConnection!.setLocalDescription(answer);

    _sendSignaling({
      'type': 'sdp_answer',
      'payload': {'sdp': answer.sdp},
    });

    print('[WebRTC] Answer sent');
  }

  /// Handle SDP answer (viewer receives from host)
  Future<void> _handleAnswer(String sdp) async {
    if (_peerConnection == null) return;
    if (sdp.isEmpty) {
      onError?.call('Received empty SDP answer');
      return;
    }

    await _peerConnection!.setRemoteDescription(
      RTCSessionDescription(sdp, 'answer'),
    );

    print('[WebRTC] Answer received');
  }

  /// Handle ICE candidate
  Future<void> _handleIceCandidate(Map<String, dynamic> data) async {
    if (_peerConnection == null) return;

    final candidate = RTCIceCandidate(
      data['candidate']?.toString(),
      data['sdpMid']?.toString(),
      data['sdpMLineIndex'] is int ? data['sdpMLineIndex'] as int : null,
    );
    await _peerConnection!.addCandidate(candidate);
  }

  /// ICE candidate event
  void _onIceCandidate(RTCIceCandidate candidate) {
    _sendSignaling({
      'type': 'ice_candidate',
      'payload': {
        'candidate': candidate.candidate,
        'sdpMid': candidate.sdpMid,
        'sdpMLineIndex': candidate.sdpMLineIndex,
      },
    });
  }

  /// Track event (receive remote stream)
  void _onTrack(RTCTrackEvent event) {
    if (event.streams.isNotEmpty) {
      _remoteStream = event.streams[0];
      onRemoteStream?.call(_remoteStream!);
      print('[WebRTC] Remote stream received');
    }
  }

  /// Send signaling message
  void _sendSignaling(Map<String, dynamic> data) {
    _wsChannel?.sink.add(json.encode(data));
  }

  /// Get remote stream for rendering
  MediaStream? get remoteStream => _remoteStream;

  /// Disconnect and cleanup
  Future<void> disconnect() async {
    _wsChannel?.sink.close();
    await _localStream?.dispose();
    await _remoteStream?.dispose();
    await _peerConnection?.close();
    
    _wsChannel = null;
    _localStream = null;
    _remoteStream = null;
    _peerConnection = null;
    
    print('[WebRTC] Disconnected');
  }
}
