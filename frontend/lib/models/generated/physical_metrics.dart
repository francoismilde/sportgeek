// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.147300



class PhysicalMetrics {
  final dynamic height;
  final dynamic weight;
  final dynamic bodyFat;
  final dynamic restingHr;
  final dynamic sleepQualityAvg;

  PhysicalMetrics({
    required this.height, required this.weight, required this.bodyFat, required this.restingHr, required this.sleepQualityAvg
  });

  factory PhysicalMetrics.fromJson(Map<String, dynamic> json) {
    return PhysicalMetrics(
      height: json['height'],
      weight: json['weight'],
      bodyFat: json['body_fat'],
      restingHr: json['resting_hr'],
      sleepQualityAvg: json['sleep_quality_avg'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'height': height,
      'weight': weight,
      'body_fat': bodyFat,
      'resting_hr': restingHr,
      'sleep_quality_avg': sleepQualityAvg,
    };
  }
}
