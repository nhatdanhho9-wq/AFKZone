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
  final String? requestId; // For host: used to call POST /remote/host-ready/{requestId}

  const RemoteSessionScreen({
    Key? key,
    required this.sessionId,
    this.isHost = false,
    this.wsToken,
    this.requestId,
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
  // 2-step host_ready flow state
  bool _waitingForHostReady = false;
  String? _pendingRequestIdForHost;
  // Per-request dedup: track handled request_id and sent flags
  String? _handledRequestId; // Request ID that has been processed
  bool _mediaProjectionDialogShown = false;
  bool _hostReadySent = false;

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
      } else if (state == RTCPeerConnectionState.RTCPeerConnectionStateClosed) {
        // Closed by remote peer or intentionally
        print('[RemoteSession] Connection closed');
        if (mounted) {
          if (widget.isHost) {
            // Host side: just close screen when peer cancels
            Navigator.of(context).pop();
          } else {
            // Viewer side: show disconnected state
            setState(() {
              _isConnected = false;
              _error = 'Session ended';
            });
          }
        }
      }
    };

    _webrtcService!.onError = (error) {
      if (error.contains('HOST_NOT_READY')) {
        setState(() {
          _error = 'Host needs to enable screen capture';
          _isConnecting = false;
        });
      } else {
        setState(() {
          _error = error;
          _isConnecting = false;
        });
      }
    };

    // 2-step host_ready flow callbacks
    _webrtcService!.onEnableScreenCapture = (requestId) {
      // Host receives: show MediaProjection dialog
      print('[RemoteSession] >>> HOST: enable_screen_capture received! requestId=$requestId');
      setState(() {
        _pendingRequestIdForHost = requestId;
      });
      _showEnableScreenCaptureDialog(requestId);
    };

    _webrtcService!.onWaitHostReady = () {
      // Controller: show waiting UI, do NOT SDP yet
      setState(() {
        _waitingForHostReady = true;
        _isConnecting = true;
      });
    };

    _webrtcService!.onHostReady = (sessionId, controllerToken) async {
      // Controller: auto-continue SDP
      print('[RemoteSession] Host ready! session=$sessionId, starting SDP...');
      setState(() {
        _waitingForHostReady = false;
      });
      // Create SDP offer and start connection
      await _webrtcService!.startViewer();
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

    // NEW CONTRACT: Host does NOT connect WS until AFTER host-ready returns token
    if (widget.isHost) {
      // Host mode: DO NOT connect WS yet!
      // 1. Show MediaProjection dialog immediately
      // 2. User clicks OK → host-ready returns host_token
      // 3. THEN connect WS with host_token
      
      if (widget.requestId == null) {
        print('[RemoteSession] HOST ERROR: requestId is required for host mode!');
        setState(() {
          _error = 'Missing requestId. Please re-approve the request.';
          _isConnecting = false;
        });
        return;
      }
      
      print('[RemoteSession] HOST: NOT connecting WS yet (no token)');
      print('[RemoteSession] HOST: Will show MediaProjection dialog, call host-ready, THEN connect WS');
      
      // Stop showing "connecting" state - we're waiting for user action
      setState(() {
        _isConnecting = false;
      });
      
      // Show MediaProjection dialog directly (don't wait for WS enable_screen_capture)
      // Use widget.requestId since we have it from approve flow
      _showEnableScreenCaptureDialog(widget.requestId!);
      
    } else {
      // Controller mode: must have token from request flow
      String? token = widget.wsToken;
      if (token == null) {
        print('[RemoteSession] CONTROLLER ERROR: No wsToken provided!');
        setState(() {
          _error = 'Missing signaling token.';
          _isConnecting = false;
        });
        return;
      }
      
      print('[RemoteSession] CONTROLLER: Connecting to signaling with token: ${token.substring(0, 20)}...');
      final connected = await _webrtcService!.connectSignaling(wsToken: token);
      if (!connected) {
        setState(() {
          _error = 'Failed to connect signaling';
          _isConnecting = false;
        });
        return;
      }
      print('[RemoteSession] CONTROLLER: Signaling connected, starting viewer...');
      await _webrtcService!.startViewer();
    }
  }

  /// Host: show MediaProjection dialog when server signals enable_screen_capture
  void _showEnableScreenCaptureDialog(String requestId) {
    // Per-request dedup: check if this request_id was already handled
    if (_handledRequestId == requestId) {
      print('[RemoteSession] >>> HOST: request_id=$requestId already handled, skipping duplicate');
      return;
    }
    
    // Prevent duplicate dialogs within same session
    if (_mediaProjectionDialogShown) {
      print('[RemoteSession] >>> HOST: Dialog already shown, skipping duplicate dialog for request=$requestId');
      return;
    }
    
    // Mark this request as being handled
    _handledRequestId = requestId;
    _mediaProjectionDialogShown = true;
    
    print('[RemoteSession] >>> HOST: Showing MediaProjection dialog for request=$requestId');
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.screen_share, color: Colors.green),
            const SizedBox(width: 12),
            const Text('Screen Sharing Request'),
          ],
        ),
        content: const Text(
          'A remote device wants to view your screen.\n\nTap "BẮT ĐẦU NGAY" to enable screen capture.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              print('[RemoteSession] >>> HOST: User cancelled MediaProjection dialog');
              Navigator.of(ctx).pop();
              _disconnect();
            },
            child: const Text('Cancel', style: TextStyle(color: Colors.red)),
          ),
          ElevatedButton(
            onPressed: () async {
              print('[RemoteSession] >>> HOST: User clicked BẮT ĐẦU NGAY');
              Navigator.of(ctx).pop();
              // Start MediaProjection and signal host_ready
              await _enableScreenCaptureAndNotify(requestId);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            child: const Text('BẮT ĐẦU NGAY', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  /// Host: trigger MediaProjection and POST /remote/host-ready
  /// NEW CONTRACT: host-ready returns host_token, then reconnect WS with token
  Future<void> _enableScreenCaptureAndNotify(String requestId) async {
    // Prevent duplicate host-ready calls
    if (_hostReadySent) {
      print('[RemoteSession] >>> HOST: host-ready already sent for this session, skipping duplicate');
      return;
    }
    
    print('[RemoteSession] >>> HOST: Starting MediaProjection capture for request=$requestId');
    try {
      // Request MediaProjection
      final stream = await navigator.mediaDevices.getDisplayMedia({
        'audio': false,
        'video': {
          'mandatory': {'minWidth': 720, 'minHeight': 1280, 'minFrameRate': 15},
        },
      });
      print('[RemoteSession] >>> HOST: MediaProjection stream obtained, tracks=${stream.getTracks().length}');
      
      // Start hosting with the captured stream
      await _webrtcService!.startHost(stream);
      print('[RemoteSession] >>> HOST: WebRTC startHost completed');
      
      // Call host-ready to get host_token
      print('[RemoteSession] >>> HOST: Calling hostReady API for request=$requestId');
      _hostReadySent = true; // Mark as sent to prevent duplicates
      final result = await RemoteService.hostReady(requestId, screenCapture: true);
      
      if (!result.success) {
        print('[RemoteSession] >>> HOST ERROR: hostReady failed: ${result.error}');
        setState(() {
          _error = 'Host ready failed: ${result.error}';
        });
        return;
      }
      
      if (result.hostToken == null || result.hostToken!.isEmpty) {
        print('[RemoteSession] >>> HOST ERROR: hostReady returned no host_token!');
        setState(() {
          _error = 'Server did not return host_token. Please try again.';
        });
        return;
      }
      
      print('[RemoteSession] >>> HOST: Got hostToken from host-ready (${result.hostToken!.length} chars)');
      print('[RemoteSession] >>> HOST: sessionId=${result.sessionId}, wsUrl=${result.signalingWsUrl ?? 'not provided'}');
      
      // NOW connect signaling WS with the host_token from host-ready
      print('[RemoteSession] >>> HOST: Connecting signaling WS with host_token...');
      final connected = await _webrtcService!.connectSignaling(wsToken: result.hostToken);
      if (!connected) {
        print('[RemoteSession] >>> HOST ERROR: Failed to connect signaling WS!');
        setState(() {
          _error = 'Failed to connect signaling with host_token';
        });
        return;
      }
      
      print('[RemoteSession] >>> HOST: Signaling WS connected! Host ready complete.');
      setState(() {
        _isConnected = true;
      });
      
    } catch (e) {
      print('[RemoteSession] >>> HOST ERROR: Enable screen capture failed: $e');
      setState(() {
        _error = 'Failed to enable screen capture: $e';
      });
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
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(color: Colors.green),
                  const SizedBox(height: 16),
                  Text(
                    _waitingForHostReady 
                        ? 'Waiting for host to enable screen capture...'
                        : 'Connecting to remote device...',
                    style: const TextStyle(color: Colors.white),
                    textAlign: TextAlign.center,
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
