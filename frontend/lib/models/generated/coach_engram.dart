// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.613778

import 'enums.dart';

class CoachEngram {
  final MemoryType type;
  final ImpactLevel impact;
  final MemoryStatus status;
  final dynamic content;
  final List<dynamic> tags;
  final dynamic endDate;
  final dynamic id;
  final dynamic memoryId;
  final dynamic author;
  final dynamic createdAt;

  CoachEngram({
    required this.type, required this.impact, required this.status, required this.content, required this.tags, required this.endDate, required this.id, required this.memoryId, required this.author, required this.createdAt
  });

  factory CoachEngram.fromJson(Map<String, dynamic> json) {
    return CoachEngram(
      type: json['type'] != null ? MemoryType.fromJson(json['type']) : MemoryType.values.first,
      impact: json['impact'] != null ? ImpactLevel.fromJson(json['impact']) : ImpactLevel.values.first,
      status: json['status'] != null ? MemoryStatus.fromJson(json['status']) : MemoryStatus.values.first,
      content: json['content'],
      tags: json['tags'] ?? [],
      endDate: json['end_date'],
      id: json['id'],
      memoryId: json['memory_id'],
      author: json['author'],
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type.toJson(),
      'impact': impact.toJson(),
      'status': status.toJson(),
      'content': content,
      'tags': tags,
      'end_date': endDate,
      'id': id,
      'memory_id': memoryId,
      'author': author,
      'created_at': createdAt,
    };
  }
}
