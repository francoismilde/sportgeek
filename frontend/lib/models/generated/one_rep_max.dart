// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.623484



class OneRepMax {
  final dynamic estimated1Rm;
  final dynamic methodUsed;

  OneRepMax({
    required this.estimated1Rm, required this.methodUsed
  });

  factory OneRepMax.fromJson(Map<String, dynamic> json) {
    return OneRepMax(
      estimated1Rm: json['estimated_1rm'],
      methodUsed: json['method_used'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'estimated_1rm': estimated1Rm,
      'method_used': methodUsed,
    };
  }
}
