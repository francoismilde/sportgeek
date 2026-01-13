
class ProfileDraft {
  static final ProfileDraft _instance = ProfileDraft._internal();

  factory ProfileDraft() {
    return _instance;
  }

  ProfileDraft._internal();

  // Stockage temporaire pour agréger les données
  Map<String, dynamic> performanceBaseline = {};
  Map<String, dynamic> constraints = {}; // Matrice hebdo
  Map<String, dynamic> injuryPrevention = {}; // Blessures
  List<String> equipment = ["Standard"];

  void clear() {
    performanceBaseline = {};
    constraints = {};
    injuryPrevention = {};
    equipment = ["Standard"];
  }
}
