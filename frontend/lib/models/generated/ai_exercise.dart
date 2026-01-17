// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.620342



class AIExercise {
  final dynamic name;
  final dynamic sets;
  final dynamic reps;
  final dynamic rest;
  final dynamic tips;
  final dynamic recordingMode;

  AIExercise({
    required this.name, required this.sets, required this.reps, required this.rest, required this.tips, required this.recordingMode
  });

  factory AIExercise.fromJson(Map<String, dynamic> json) {
    return AIExercise(
      name: json['name'],
      sets: json['sets'],
      reps: json['reps'],
      rest: json['rest'],
      tips: json['tips'],
      recordingMode: json['recording_mode'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'sets': sets,
      'reps': reps,
      'rest': rest,
      'tips': tips,
      'recording_mode': recordingMode,
    };
  }
}
