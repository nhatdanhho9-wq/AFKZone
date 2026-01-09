import 'package:flutter/material.dart';
import '../services/remote_service.dart';
import 'remote_session.dart';
import '../services/device_service.dart';

/// Pending Requests Screen for Remote Preview v0.1
/// Shows pending remote requests for owner to approve/reject
class PendingRequestsScreen extends StatefulWidget {
  const PendingRequestsScreen({Key? key}) : super(key: key);

  @override
  State<PendingRequestsScreen> createState() => _PendingRequestsScreenState();
}

class _PendingRequestsScreenState extends State<PendingRequestsScreen> {
  List<PendingRequest> _requests = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRequests();
  }

  Future<void> _loadRequests() async {
    setState(() => _isLoading = true);
    final requests = await RemoteService.getPending();
    setState(() {
      _requests = requests;
      _isLoading = false;
    });
  }

  Future<void> _approve(PendingRequest request) async {
    final result = await RemoteService.approve(request.requestId);
    if (result.success && result.sessionId != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Approved! Session: ${result.sessionId}')),
      );
      // If the approving device is ALSO the target host device, it can attach and start sharing immediately.
      // Otherwise (owner approves from another device), the target host device will poll /sessions/host/attach
      // and show the screen-share prompt locally.
      final hostDeviceId = DeviceService.deviceId;
      if (hostDeviceId != null) {
        final attach = await RemoteService.hostAttach(hostDeviceId: hostDeviceId);
        if (attach.success && attach.hostToken != null) {
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
              builder: (_) => RemoteSessionScreen(
                sessionId: result.sessionId!,
                isHost: true,
                wsToken: attach.hostToken!,
              ),
            ),
          );
          return;
        }
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Approve failed: ${result.error}')),
      );
    }
    _loadRequests();
  }

  Future<void> _reject(PendingRequest request) async {
    final success = await RemoteService.reject(request.requestId);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(success ? 'Rejected' : 'Reject failed')),
    );
    _loadRequests();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pending Requests'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRequests,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _requests.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.inbox_outlined, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('No pending requests', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadRequests,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _requests.length,
                    itemBuilder: (context, index) {
                      final request = _requests[index];
                      return _buildRequestCard(request);
                    },
                  ),
                ),
    );
  }

  Widget _buildRequestCard(PendingRequest request) {
    final subtitle = (request.requesterDeviceId != null && request.requesterDeviceId!.isNotEmpty)
        ? 'From device: ${request.requesterDeviceId}'
        : (request.requesterAccountId != null ? 'From account: ${request.requesterAccountId}' : 'From: unknown');
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const CircleAvatar(
                  backgroundColor: Colors.green,
                  child: Icon(Icons.person, color: Colors.white),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        request.requesterName ?? 'Remote Request',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      Text(subtitle, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                      Text(
                        'Request ID: ${request.requestId.substring(0, 8)}...',
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.orange.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    request.status.toUpperCase(),
                    style: TextStyle(
                      color: Colors.orange.shade800,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'Requested: ${request.createdAt}',
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: () => _reject(request),
                  icon: const Icon(Icons.close, color: Colors.red),
                  label: const Text('Reject', style: TextStyle(color: Colors.red)),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: () => _approve(request),
                  icon: const Icon(Icons.check),
                  label: const Text('Approve'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
