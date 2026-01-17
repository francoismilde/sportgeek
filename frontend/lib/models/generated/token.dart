// GÉNÉRÉ AUTOMATIQUEMENT
// Timestamp : 2026-01-17T08:56:00.140755



class Token {
  final dynamic accessToken;
  final dynamic tokenType;

  Token({
    required this.accessToken, required this.tokenType
  });

  factory Token.fromJson(Map<String, dynamic> json) {
    return Token(
      accessToken: json['access_token'],
      tokenType: json['token_type'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'token_type': tokenType,
    };
  }
}
