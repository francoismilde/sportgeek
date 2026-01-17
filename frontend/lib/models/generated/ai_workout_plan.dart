// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.618409

import 'ai_exercise.dart';

class AIWorkoutPlan {
  final dynamic title;
  final dynamic coachComment;
  final List<dynamic> warmup;
  final List<AIExercise> exercises;
  final List<dynamic> cooldown;

  AIWorkoutPlan({
    required this.title, required this.coachComment, required this.warmup, required this.exercises, required this.cooldown
  });

  factory AIWorkoutPlan.fromJson(Map<String, dynamic> json) {
    return AIWorkoutPlan(
      title: json['title'],
      coachComment: json['coach_comment'],
      warmup: json['warmup'] ?? [],
      exercises: (json['exercises'] as List?)?.map((e) => AIExercise.fromJson(e)).toList() ?? [],
      cooldown: json['cooldown'] ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'coach_comment': coachComment,
      'warmup': warmup,
      'exercises': exercises.map((e) => e.toJson()).toList(),
      'cooldown': cooldown,
    };
  }
}
