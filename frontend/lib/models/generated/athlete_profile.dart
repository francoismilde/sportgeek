// GÉNÉRÉ AUTOMATIQUEMENT - NE PAS MODIFIER
// Timestamp : 2026-01-16T20:05:54.515891

import 'enums.dart';

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
  final dynamic? createdAt;
  final dynamic? updatedAt;

  AthleteProfile({
    required this.basicInfo, required this.physicalMetrics, required this.sportContext, required this.trainingPreferences, required this.goals, required this.constraints, required this.injuryPrevention, required this.performanceBaseline, required this.id, required this.userId, this.createdAt, this.updatedAt
  });

  factory AthleteProfile.fromJson(Map<String, dynamic> json) {
    return AthleteProfile(
      basicInfo: json['basic_info'] != null ? BasicInfo.fromJson(json['basic_info']) : null,
      physicalMetrics: json['physical_metrics'] != null ? PhysicalMetrics.fromJson(json['physical_metrics']) : null,
      sportContext: json['sport_context'] != null ? SportContext.fromJson(json['sport_context']) : null,
      trainingPreferences: json['training_preferences'] != null ? TrainingPreferences.fromJson(json['training_preferences']) : null,
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
      'basic_info': basicInfo?.toJson(),
      'physical_metrics': physicalMetrics?.toJson(),
      'sport_context': sportContext?.toJson(),
      'training_preferences': trainingPreferences?.toJson(),
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
