// GÉNÉRÉ AUTOMATIQUEMENT - NE PAS MODIFIER
// Timestamp : 2026-01-16T20:05:54.523303

import 'enums.dart';

class WorkoutSession {
  final dynamic date;
  final dynamic duration;
  final dynamic rpe;
  final dynamic energyLevel;
  final dynamic? notes;
  final dynamic? aiAnalysis;
  final List<WorkoutSet> sets;
  final dynamic id;

  WorkoutSession({
    required this.date, required this.duration, required this.rpe, required this.energyLevel, this.notes, this.aiAnalysis, required this.sets, required this.id
  });

  factory WorkoutSession.fromJson(Map<String, dynamic> json) {
    return WorkoutSession(
      date: json['date'],
      duration: json['duration'],
      rpe: json['rpe'],
      energyLevel: json['energy_level'],
      notes: json['notes'],
      aiAnalysis: json['ai_analysis'],
      sets: (json['sets'] as List?)?.map((e) => WorkoutSet.fromJson(e)).toList() ?? [],
      id: json['id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'duration': duration,
      'rpe': rpe,
      'energy_level': energyLevel,
      'notes': notes,
      'ai_analysis': aiAnalysis,
      'sets': sets?.map((e) => e.toJson()).toList(),
      'id': id,
    };
  }
}
