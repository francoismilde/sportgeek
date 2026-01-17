// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.621806



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
