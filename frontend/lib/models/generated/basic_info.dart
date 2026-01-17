// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.605472



class BasicInfo {
  final dynamic pseudo;
  final dynamic email;
  final dynamic birthDate;
  final dynamic trainingAge;
  final dynamic biologicalSex;

  BasicInfo({
    required this.pseudo, required this.email, required this.birthDate, required this.trainingAge, required this.biologicalSex
  });

  factory BasicInfo.fromJson(Map<String, dynamic> json) {
    return BasicInfo(
      pseudo: json['pseudo'],
      email: json['email'],
      birthDate: json['birth_date'],
      trainingAge: json['training_age'],
      biologicalSex: json['biological_sex'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pseudo': pseudo,
      'email': email,
      'birth_date': birthDate,
      'training_age': trainingAge,
      'biological_sex': biologicalSex,
    };
  }
}
