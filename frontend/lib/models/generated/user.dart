// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-16T20:28:24.599658



class User {
  final dynamic id;
  final dynamic username;
  final dynamic email;
  final dynamic profileData;

  User({
    required this.id, required this.username, required this.email, required this.profileData
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      profileData: json['profile_data'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'profile_data': profileData,
    };
  }
}
