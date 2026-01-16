// GÉNÉRÉ AUTOMATIQUEMENT - NE PAS MODIFIER
// Timestamp : 2026-01-16T20:05:54.529169

import 'enums.dart';

class FeedItem {
  final FeedItemType type;
  final dynamic title;
  final dynamic message;
  final dynamic priority;
  final dynamic? actionPayload;
  final dynamic id;
  final dynamic isRead;
  final dynamic isCompleted;
  final dynamic createdAt;

  FeedItem({
    required this.type, required this.title, required this.message, required this.priority, this.actionPayload, required this.id, required this.isRead, required this.isCompleted, required this.createdAt
  });

  factory FeedItem.fromJson(Map<String, dynamic> json) {
    return FeedItem(
      type: json['type'] != null ? FeedItemType.fromJson(json['type']) : null ?? FeedItemType.values.first,
      title: json['title'],
      message: json['message'],
      priority: json['priority'],
      actionPayload: json['action_payload'],
      id: json['id'],
      isRead: json['is_read'],
      isCompleted: json['is_completed'],
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type?.toJson(),
      'title': title,
      'message': message,
      'priority': priority,
      'action_payload': actionPayload,
      'id': id,
      'is_read': isRead,
      'is_completed': isCompleted,
      'created_at': createdAt,
    };
  }
}
