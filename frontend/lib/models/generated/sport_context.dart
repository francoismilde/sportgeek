// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.607969

import 'enums.dart';

class SportContext {
  final SportType sport;
  final dynamic position;
  final dynamic level;
  final List<EquipmentType> equipment;

  SportContext({
    required this.sport, required this.position, required this.level, required this.equipment
  });

  factory SportContext.fromJson(Map<String, dynamic> json) {
    return SportContext(
      sport: json['sport'] != null ? SportType.fromJson(json['sport']) : SportType.values.first,
      position: json['position'],
      level: json['level'],
      equipment: json['equipment'] ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'sport': sport.toJson(),
      'position': position,
      'level': level,
      'equipment': equipment,
    };
  }
}
