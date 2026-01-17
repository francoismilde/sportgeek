// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.151071

import 'coach_engram.dart';

class CoachMemory {
  final dynamic id;
  final dynamic currentContext;
  final dynamic currentPhase;
  final dynamic flags;
  final dynamic insights;
  final List<CoachEngram> engrams;

  CoachMemory({
    required this.id, required this.currentContext, required this.currentPhase, required this.flags, required this.insights, required this.engrams
  });

  factory CoachMemory.fromJson(Map<String, dynamic> json) {
    return CoachMemory(
      id: json['id'],
      currentContext: json['current_context'],
      currentPhase: json['current_phase'],
      flags: json['flags'],
      insights: json['insights'],
      engrams: (json['engrams'] as List?)?.map((e) => CoachEngram.fromJson(e)).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'current_context': currentContext,
      'current_phase': currentPhase,
      'flags': flags,
      'insights': insights,
      'engrams': engrams.map((e) => e.toJson()).toList(),
    };
  }
}
