// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.624022



class ACWR {
  final dynamic ratio;
  final dynamic status;
  final dynamic color;
  final dynamic message;

  ACWR({
    required this.ratio, required this.status, required this.color, required this.message
  });

  factory ACWR.fromJson(Map<String, dynamic> json) {
    return ACWR(
      ratio: json['ratio'],
      status: json['status'],
      color: json['color'],
      message: json['message'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ratio': ratio,
      'status': status,
      'color': color,
      'message': message,
    };
  }
}
