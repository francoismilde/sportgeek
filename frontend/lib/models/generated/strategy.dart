// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.159652



class Strategy {
  final dynamic periodizationTitle;
  final List<dynamic> phases;

  Strategy({
    required this.periodizationTitle, required this.phases
  });

  factory Strategy.fromJson(Map<String, dynamic> json) {
    return Strategy(
      periodizationTitle: json['periodization_title'],
      phases: json['phases'] ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'periodization_title': periodizationTitle,
      'phases': phases,
    };
  }
}
