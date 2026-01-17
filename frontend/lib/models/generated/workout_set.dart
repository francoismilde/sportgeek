// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.156421



class WorkoutSet {
  final dynamic exerciseName;
  final dynamic setOrder;
  final dynamic weight;
  final dynamic reps;
  final dynamic rpe;
  final dynamic restSeconds;
  final dynamic metricType;
  final dynamic id;

  WorkoutSet({
    required this.exerciseName, required this.setOrder, required this.weight, required this.reps, required this.rpe, required this.restSeconds, required this.metricType, required this.id
  });

  factory WorkoutSet.fromJson(Map<String, dynamic> json) {
    return WorkoutSet(
      exerciseName: json['exercise_name'],
      setOrder: json['set_order'],
      weight: json['weight'],
      reps: json['reps'],
      rpe: json['rpe'],
      restSeconds: json['rest_seconds'],
      metricType: json['metric_type'],
      id: json['id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'exercise_name': exerciseName,
      'set_order': setOrder,
      'weight': weight,
      'reps': reps,
      'rpe': rpe,
      'rest_seconds': restSeconds,
      'metric_type': metricType,
      'id': id,
    };
  }
}
