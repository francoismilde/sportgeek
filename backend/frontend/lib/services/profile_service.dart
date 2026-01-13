
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'auth_service.dart';

class ProfileService {
  final String baseUrl = AuthService.baseUrl;

  Future<bool> saveCompleteProfile(Map<String, dynamic> profileJson) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null) {
      print("⛔ Pas de token trouvé");
      return false;
    }

    print("🚀 [PROFILE] Envoi du JSON...");
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/profiles/complete'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(profileJson),
      );

      print("📡 Status: ${response.statusCode}");
      if (response.statusCode == 200 || response.statusCode == 201) {
        return true;
      }
      print("❌ Erreur Backend: ${response.body}");
      return false;
    } catch (e) {
      print("🔥 Exception Réseau: $e");
      return false;
    }
  }
}
