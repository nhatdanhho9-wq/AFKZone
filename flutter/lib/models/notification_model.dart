class AppNotification {
  final int id;
  final String title;
  final String message;
  final String type;
  final DateTime createdAt;
  final DateTime? expiresAt;
  final bool isRead;

  AppNotification({required this.id, required this.title, required this.message, required this.type, required this.createdAt, this.expiresAt, this.isRead = false});
}
