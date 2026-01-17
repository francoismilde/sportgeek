// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.165282

enum MemoryType {
  INJURY_REPORT,
  LIFE_CONSTRAINT,
  STRATEGIC_OVERRIDE,
  BIOFEEDBACK_LOG;

  String toJson() => name;
  static MemoryType fromJson(dynamic json) {
    return MemoryType.values.firstWhere((e) => e.name == json.toString(), orElse: () => INJURY_REPORT);
  }
}

enum ImpactLevel {
  SEVERE,
  MODERATE,
  INFO;

  String toJson() => name;
  static ImpactLevel fromJson(dynamic json) {
    return ImpactLevel.values.firstWhere((e) => e.name == json.toString(), orElse: () => SEVERE);
  }
}

enum MemoryStatus {
  ACTIVE,
  RESOLVED,
  ARCHIVED,
  FORGOTTEN;

  String toJson() => name;
  static MemoryStatus fromJson(dynamic json) {
    return MemoryStatus.values.firstWhere((e) => e.name == json.toString(), orElse: () => ACTIVE);
  }
}

enum FeedItemType {
  INFO,
  ANALYSIS,
  ACTION,
  ALERT,
  WORKOUT_LOG,
  COACH_INSIGHT,
  PERSONAL_RECORD,
  SYSTEM_ALERT,
  DAILY_TIP;

  String toJson() => name;
  static FeedItemType fromJson(dynamic json) {
    return FeedItemType.values.firstWhere((e) => e.name == json.toString(), orElse: () => INFO);
  }
}

enum SportType {
  RUGBY,
  FOOTBALL,
  CROSSFIT,
  HYBRID,
  RUNNING,
  OTHER,
  BODYBUILDING,
  CYCLING,
  TRIATHLON,
  POWERLIFTING,
  SWIMMING,
  COMBAT_SPORTS;

  String toJson() => name;
  static SportType fromJson(dynamic json) {
    return SportType.values.firstWhere((e) => e.name == json.toString(), orElse: () => COMBAT_SPORTS);
  }
}

enum EquipmentType {
  PERFORMANCE_LAB,
  COMMERCIAL_GYM,
  HOME_GYM_BARBELL,
  HOME_GYM_DUMBBELL,
  CALISTHENICS_KIT,
  BODYWEIGHT_ZERO,
  ENDURANCE_SUITE,
  STANDARD,
  HOME_GYM_FULL,
  CROSSFIT_BOX,
  DUMBBELLS,
  BARBELL,
  KETTLEBELLS,
  PULL_UP_BAR,
  BENCH,
  DIP_STATION,
  BANDS,
  RINGS_TRX,
  JUMP_ROPE,
  WEIGHT_VEST,
  BIKE,
  HOME_TRAINER,
  ROWER,
  TREADMILL,
  POOL;

  String toJson() => name;
  static EquipmentType fromJson(dynamic json) {
    return EquipmentType.values.firstWhere((e) => e.name == json.toString(), orElse: () => PERFORMANCE_LAB);
  }
}

