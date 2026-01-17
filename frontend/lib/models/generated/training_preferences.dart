// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.608890



class TrainingPreferences {
  final List<dynamic> daysAvailable;
  final dynamic durationMin;
  final dynamic preferredSplit;

  TrainingPreferences({
    required this.daysAvailable, required this.durationMin, required this.preferredSplit
  });

  factory TrainingPreferences.fromJson(Map<String, dynamic> json) {
    return TrainingPreferences(
      daysAvailable: json['days_available'] ?? [],
      durationMin: json['duration_min'],
      preferredSplit: json['preferred_split'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'days_available': daysAvailable,
      'duration_min': durationMin,
      'preferred_split': preferredSplit,
    };
  }
}
