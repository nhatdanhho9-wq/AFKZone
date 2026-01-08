import 'dart:async';
import 'package:flutter/services.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'remote_service.dart';
import 'webrtc_service.dart';

/// Host Service for Remote Preview v0.1
/// Handles: MediaProjection screen capture, session attach, video publish
class HostService {
  static const MethodChannel _channel = MethodChannel('com.afkzone.remote/host');
  
  WebRTCService? _webrtcService;
  MediaStream? _screenStream;
  bool _isHosting = false;

  Function(String)? onError;
  Function()? onSessionEnded;

  /// Attach to session as host and start screen capture
  Future<bool> attachToSession(String sessionId) async {
    try {
      // Attach via API
      final headers = await RemoteService.getTurnCredentials(sessionId);
      if (headers == null) {
        onError?.call('Failed to get session credentials');
        return false;
      }

      // Initialize WebRTC
      _webrtcService = WebRTCService(sessionId: sessionId, isHost: true);
      
      _webrtcService!.onError = (error) {
        onError?.call(error);
      };

      final initialized = await _webrtcService!.initialize();
      if (!initialized) {
        onError?.call('Failed to initialize WebRTC');
        return false;
      }

      final connected = await _webrtcService!.connectSignaling();
      if (!connected) {
        onError?.call('Failed to connect signaling');
        return false;
      }

      // Start screen capture
      final started = await startScreenCapture();
      if (!started) {
        onError?.call('Failed to start screen capture');
        return false;
      }

      // Start as host
      await _webrtcService!.startHost(_screenStream!);
      
      _isHosting = true;
      print('[HostService] Attached to session: $sessionId');
      return true;
    } catch (e) {
      print('[HostService] Attach error: $e');
      onError?.call(e.toString());
      return false;
    }
  }

  /// Start screen capture via MediaProjection
  Future<bool> startScreenCapture() async {
    try {
      // Request screen capture permission
      final Map<String, dynamic> mediaConstraints = {
        'audio': false,
        'video': {
          'mandatory': {
            'minWidth': 720,
            'minHeight': 1280,
            'minFrameRate': 15,
          },
        },
      };

      _screenStream = await navigator.mediaDevices.getDisplayMedia(mediaConstraints);
      
      if (_screenStream == null || _screenStream!.getVideoTracks().isEmpty) {
        print('[HostService] No screen stream available');
        return false;
      }

      // Handle track ended (user stopped sharing)
      _screenStream!.getVideoTracks().first.onEnded = () {
        print('[HostService] Screen capture ended');
        stopHosting();
        onSessionEnded?.call();
      };

      print('[HostService] Screen capture started');
      return true;
    } catch (e) {
      print('[HostService] Screen capture error: $e');
      return false;
    }
  }

  /// Stop hosting and cleanup
  Future<void> stopHosting() async {
    _isHosting = false;
    
    await _screenStream?.dispose();
    await _webrtcService?.disconnect();
    
    _screenStream = null;
    _webrtcService = null;
    
    print('[HostService] Stopped hosting');
  }

  /// Check if currently hosting
  bool get isHosting => _isHosting;
}
