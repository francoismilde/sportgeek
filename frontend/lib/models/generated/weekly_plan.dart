// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.159156



class WeeklyPlan {
  final List<dynamic> schedule;
  final dynamic reasoning;

  WeeklyPlan({
    required this.schedule, required this.reasoning
  });

  factory WeeklyPlan.fromJson(Map<String, dynamic> json) {
    return WeeklyPlan(
      schedule: json['schedule'] ?? [],
      reasoning: json['reasoning'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'schedule': schedule,
      'reasoning': reasoning,
    };
  }
}
