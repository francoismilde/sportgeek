// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.161331

import 'coach_engram.dart';

class ProfileAudit {
  final dynamic markdownReport;
  final List<CoachEngram> generatedEngrams;

  ProfileAudit({
    required this.markdownReport, required this.generatedEngrams
  });

  factory ProfileAudit.fromJson(Map<String, dynamic> json) {
    return ProfileAudit(
      markdownReport: json['markdown_report'],
      generatedEngrams: (json['generated_engrams'] as List?)?.map((e) => CoachEngram.fromJson(e)).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'markdown_report': markdownReport,
      'generated_engrams': generatedEngrams.map((e) => e.toJson()).toList(),
    };
  }
}
