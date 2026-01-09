import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import '../services/webrtc_service.dart';
import '../services/remote_service.dart';
import '../services/device_service.dart';

/// Remote Session Screen for Remote Preview v0.1
/// Displays remote video stream from host
class RemoteSessionScreen extends StatefulWidget {
  final String sessionId;
  final bool isHost;
  final String? wsToken; // controller_token or host_token depending on role

  const RemoteSessionScreen({
    Key? key,
    required this.sessionId,
    this.isHost = false,
    this.wsToken,
  }) : super(key: key);

  @override
  State<RemoteSessionScreen> createState() => _RemoteSessionScreenState();
}

class _RemoteSessionScreenState extends State<RemoteSessionScreen> {
  WebRTCService? _webrtcService;
  RTCVideoRenderer _remoteRenderer = RTCVideoRenderer();
  bool _isConnecting = true;
  bool _isConnected = false;
  String? _error;
  // Debug state
  String _iceState = 'new';
  int _trackCount = 0;
  bool _hasVideoTrack = false;

  @override
  void initState() {
    super.initState();
    _initSession();
  }

  Future<void> _initSession() async {
    await _remoteRenderer.initialize();
    
    _webrtcService = WebRTCService(
      sessionId: widget.sessionId,
      isHost: widget.isHost,
    );

    _webrtcService!.onRemoteStream = (stream) {
      final videoTracks = stream.getVideoTracks();
      final audioTracks = stream.getAudioTracks();
      print('[RemoteSession] onRemoteStream: video=${videoTracks.length}, audio=${audioTracks.length}');
      setState(() {
        _remoteRenderer.srcObject = stream;
        _isConnected = true;
        _isConnecting = false;
        _trackCount = videoTracks.length + audioTracks.length;
        _hasVideoTrack = videoTracks.isNotEmpty;
      });
      // Check for no video track error
      if (videoTracks.isEmpty && !widget.isHost) {
        setState(() {
          _error = 'Connected but no video track received from host.';
        });
      }
    };

    _webrtcService!.onConnectionState = (state) {
      print('[RemoteSession] ICE state: $state');
      setState(() {
        _iceState = state.toString().split('.').last;
      });
      if (state == RTCPeerConnectionState.RTCPeerConnectionStateConnected) {
        setState(() {
          _isConnected = true;
          _isConnecting = false;
        });
      } else if (state == RTCPeerConnectionState.RTCPeerConnectionStateFailed ||
                 state == RTCPeerConnectionState.RTCPeerConnectionStateDisconnected) {
        setState(() {
          _isConnected = false;
          _error = 'Connection failed';
        });
      }
    };

    _webrtcService!.onError = (error) {
      setState(() {
        _error = error;
        _isConnecting = false;
      });
    };

    // Initialize WebRTC
    final initialized = await _webrtcService!.initialize();
    if (!initialized) {
      setState(() {
        _error = 'Failed to initialize WebRTC';
        _isConnecting = false;
      });
      return;
    }

    String? token = widget.wsToken;
    // If hosting and token not provided, attach to session to obtain host_token.
    if (widget.isHost && token == null) {
      final hostDeviceId = DeviceService.deviceId;
      if (hostDeviceId == null) {
        setState(() {
          _error = 'Device not registered. Please login again.';
          _isConnecting = false;
        });
        return;
      }
      final attach = await RemoteService.hostAttach(hostDeviceId: hostDeviceId);
      if (!attach.success || attach.hostToken == null) {
        setState(() {
          _error = 'Host attach failed: ${attach.error}';
          _isConnecting = false;
        });
        return;
      }
      token = attach.hostToken!;
    }

    // Connect signaling using proper token (controller_token or host_token)
    if (token == null) {
      setState(() {
        _error = 'Missing signaling token';
        _isConnecting = false;
      });
      return;
    }
    final connected = await _webrtcService!.connectSignaling(wsToken: token);
    if (!connected) {
      setState(() {
        _error = 'Failed to connect signaling';
        _isConnecting = false;
      });
      return;
    }

    // Start as viewer/host
    if (!widget.isHost) {
      await _webrtcService!.startViewer();
    } else {
      final stream = await navigator.mediaDevices.getDisplayMedia({
        'audio': false,
        'video': {
          'mandatory': {'minWidth': 720, 'minHeight': 1280, 'minFrameRate': 15},
        },
      });
      await _webrtcService!.startHost(stream);
    }
  }

  Future<void> _disconnect() async {
    await _webrtcService?.disconnect();
    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  void dispose() {
    _webrtcService?.disconnect();
    _remoteRenderer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text('Session: ${widget.sessionId.substring(0, 8)}...'),
        actions: [
          // Connection status indicator
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _isConnected 
                        ? Colors.green 
                        : (_isConnecting ? Colors.orange : Colors.red),
                  ),
                ),
                const SizedBox(width: 8),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _isConnected ? 'Connected' : (_isConnecting ? 'Connecting...' : 'Disconnected'),
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
                    ),
                    // Debug: ICE state + track count
                    Text(
                      'ICE: $_iceState | Tracks: $_trackCount',
                      style: TextStyle(fontSize: 9, color: Colors.grey.shade400),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          // Remote video
          if (_isConnected)
            RTCVideoView(
              _remoteRenderer,
              objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain,
            )
          else if (_isConnecting)
            const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Colors.green),
                  SizedBox(height: 16),
                  Text(
                    'Connecting to remote device...',
                    style: TextStyle(color: Colors.white),
                  ),
                ],
              ),
            )
          else if (_error != null)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red, size: 56),
                    const SizedBox(height: 20),
                    Text(
                      _error!.contains('not connected') || _error!.contains('Peer')
                          ? 'Peer Not Connected'
                          : 'Connection Failed',
                      style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _error!,
                      style: TextStyle(color: Colors.grey.shade400, fontSize: 14),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Session: ${widget.sessionId.substring(0, 12)}...',
                      style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                    ),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        OutlinedButton.icon(
                          onPressed: _disconnect,
                          icon: const Icon(Icons.arrow_back),
                          label: const Text('Back'),
                          style: OutlinedButton.styleFrom(foregroundColor: Colors.white),
                        ),
                        const SizedBox(width: 16),
                        ElevatedButton.icon(
                          onPressed: () {
                            print('[RemoteSession] Retry - session: ${widget.sessionId}');
                            setState(() {
                              _error = null;
                              _isConnecting = true;
                            });
                            _initSession();
                          },
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

          // Disconnect button
          Positioned(
            bottom: 32,
            left: 0,
            right: 0,
            child: Center(
              child: FloatingActionButton.extended(
                onPressed: _disconnect,
                backgroundColor: Colors.red,
                icon: const Icon(Icons.call_end),
                label: const Text('Disconnect'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
