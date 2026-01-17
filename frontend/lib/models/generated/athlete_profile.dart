// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.604398

import 'basic_info.dart';
import 'physical_metrics.dart';
import 'sport_context.dart';
import 'training_preferences.dart';

class AthleteProfile {
  final BasicInfo basicInfo;
  final PhysicalMetrics physicalMetrics;
  final SportContext sportContext;
  final TrainingPreferences trainingPreferences;
  final dynamic goals;
  final dynamic constraints;
  final dynamic injuryPrevention;
  final dynamic performanceBaseline;
  final dynamic id;
  final dynamic userId;
  final dynamic createdAt;
  final dynamic updatedAt;

  AthleteProfile({
    required this.basicInfo, required this.physicalMetrics, required this.sportContext, required this.trainingPreferences, required this.goals, required this.constraints, required this.injuryPrevention, required this.performanceBaseline, required this.id, required this.userId, required this.createdAt, required this.updatedAt
  });

  factory AthleteProfile.fromJson(Map<String, dynamic> json) {
    return AthleteProfile(
      basicInfo: BasicInfo.fromJson(json['basic_info'] ?? {}),
      physicalMetrics: PhysicalMetrics.fromJson(json['physical_metrics'] ?? {}),
      sportContext: SportContext.fromJson(json['sport_context'] ?? {}),
      trainingPreferences: TrainingPreferences.fromJson(json['training_preferences'] ?? {}),
      goals: json['goals'],
      constraints: json['constraints'],
      injuryPrevention: json['injury_prevention'],
      performanceBaseline: json['performance_baseline'],
      id: json['id'],
      userId: json['user_id'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'basic_info': basicInfo.toJson(),
      'physical_metrics': physicalMetrics.toJson(),
      'sport_context': sportContext.toJson(),
      'training_preferences': trainingPreferences.toJson(),
      'goals': goals,
      'constraints': constraints,
      'injury_prevention': injuryPrevention,
      'performance_baseline': performanceBaseline,
      'id': id,
      'user_id': userId,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}
