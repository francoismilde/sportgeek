// GÉNÉRÉ AUTOMATIQUEMENT - NE PAS MODIFIER
// Timestamp : 2026-01-16T20:05:54.528137

import 'enums.dart';

class ProfileAudit {
  final dynamic markdownReport;

  ProfileAudit({
    required this.markdownReport
  });

  factory ProfileAudit.fromJson(Map<String, dynamic> json) {
    return ProfileAudit(
      markdownReport: json['markdown_report'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'markdown_report': markdownReport,
    };
  }
}
