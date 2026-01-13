import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'bio_calibration_screen.dart';
import 'weekly_matrix_screen.dart';
import 'equipment_health_screen.dart';
import '../models/profile_draft.dart'; // <--- AJOUT
import '../services/profile_service.dart'; // <--- AJOUT

class ProfileSetupScreen extends StatefulWidget {
  const ProfileSetupScreen({super.key});

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _profileService = ProfileService(); // <--- SERVICE
  bool _isSaving = false;

  // --- CONTROLLERS & STATE ---
  final TextEditingController _pseudoController = TextEditingController(text: "Alexandre");
  String _gender = "Homme";
  int _age = 30;
  double _weight = 75.0;
  int _height = 180;
  String? _selectedLevel;
  String? _selectedSport;
  String? _selectedSpecialty;

  final List<String> _genders = ["Homme", "Femme", "Autre"];
  final Map<String, String> _levels = {
    "Débutant": "Apprentissage des mouvements, faible capacité",
    "Intermédiaire": "Pratique régulière, technique acquise",
    "Avancé": "Performance compétitive, gros volume",
    "Expert / Élite": "Niveau national/inter, optimisation marginale",
  };
  final Map<String, List<String>> _sportsSpecs = {
    "Running (Route / Piste)": ["Sprint (100m - 400m)", "Demi-fond (800m - 3000m)", "Fond (5km - 10km)", "Marathon / Semi-Marathon", "VMA & Piste générale"],
    "Trail / Ultra-Trail": ["Trail Court (< 40km)", "Ultra-Trail (> 80km)", "Kilomètre Vertical (KV)", "Skyrunning"],
    "Cyclisme (Route / VTT)": ["Grimpeur (Montagne)", "Sprinteur", "Rouleur / Contre-la-montre", "Cyclosportive (Endurance)", "VTT Cross-Country (XC)", "VTT Enduro / Descente", "Gravel"],
    "Triathlon / Ironman": ["Sprint / Olympique (Courte distance)", "Half-Ironman (70.3)", "Ironman (Full Distance)", "Duathlon"],
    "Musculation / Bodybuilding": ["Hypertrophie (Prise de masse)", "Esthétique (Men's Physique / Bikini)", "Préparation Générale"],
    "Powerlifting / Force Athlétique": ["Force Maximale (SBD)", "Bench Press Specialist", "Strongman"],
    "CrossFit / Hyrox": ["CrossFit (WOD & Skills)", "Hyrox / Fitness Racing", "Conditionning pur"],
    "Natation": ["Vitesse (50m - 100m)", "Demi-fond (200m - 400m)", "Eau Libre / Longue distance"],
    "Sports de Combat": ["MMA / Grappling", "Boxe Anglaise / Pieds-Poings", "Judo / Lutte (Prépa Physique)"],
    "Autre": ["Général / Remise en forme"]
  };

  // --- SAVE PROFILE (LE COEUR DU SYSTÈME) ---
  Future<void> _submitProfile() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isSaving = true);

      // 1. Récupération des données du brouillon (Singleton)
      final draft = ProfileDraft();

      // 2. Construction du JSON final pour l'API
      final Map<String, dynamic> payload = {
        "basic_info": {
          "pseudo": _pseudoController.text,
          "birth_date": "${DateTime.now().year - _age}-01-01",
          "training_age": 2 // Valeur par défaut si non demandée
        },
        "physical_metrics": {
          "weight": _weight,
          "height": _height.toDouble(),
          "sleep_quality_avg": 7
        },
        "sport_context": {
          "sport": _selectedSport ?? "Autre",
          "level": _selectedLevel ?? "Intermédiaire",
          "position": _selectedSpecialty,
          "equipment": draft.equipment // Vient de EquipmentScreen
        },
        "training_preferences": {
          "duration_min": 60,
          "preferred_split": "Upper/Lower"
        },
        // Les sous-structures venant des autres écrans
        "performance_baseline": draft.performanceBaseline,
        "constraints": draft.constraints,
        "injury_prevention": draft.injuryPrevention,
        "goals": {
          "primary_goal": "Optimisation Performance"
        }
      };

      // 3. Appel API
      final success = await _profileService.saveCompleteProfile(payload);

      setState(() => _isSaving = false);

      if (success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Profil Athlète mis à jour. Calibrage IA en cours..."), backgroundColor: Color(0xFF32D74B)));
          Navigator.pop(context);
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("❌ Erreur de sauvegarde"), backgroundColor: Colors.red));
        }
      }
    }
  }

  void _goToLab() => Navigator.push(context, MaterialPageRoute(builder: (context) => const BioCalibrationScreen()));
  void _goToMatrix() => Navigator.push(context, MaterialPageRoute(builder: (context) => const WeeklyMatrixScreen()));
  void _goToEquipment() => Navigator.push(context, MaterialPageRoute(builder: (context) => const EquipmentHealthScreen()));

  @override
  Widget build(BuildContext context) {
    // Style ISO
    final Color voltYellow = const Color(0xFFCCFF00);
    final Color cardBg = const Color(0xFF1C1C1E);
    final Color textWhite = const Color(0xFFFFFFFF);

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(backgroundColor: Colors.black, title: Text("IDENTITÉ ATHLÉTIQUE", style: GoogleFonts.bebasNeue(fontSize: 24, letterSpacing: 2, color: textWhite)), leading: IconButton(icon: const Icon(Icons.arrow_back_ios, color: Colors.white), onPressed: () => Navigator.pop(context))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _sectionTitle("INFOS DE BASE"),
              Row(children: [Expanded(flex: 3, child: _buildTextField("Pseudo", _pseudoController)), const SizedBox(width: 16), Expanded(flex: 2, child: _buildDropdown("Genre", _genders, _gender, (val) => setState(() => _gender = val!)))]),
              const SizedBox(height: 24),
              _sectionTitle("ANTHROPOMÉTRIE"),
              Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: cardBg, borderRadius: BorderRadius.circular(16)), child: Column(children: [_buildStepperRow("Âge", "$_age ans", onMinus: () => setState(() => _age = (_age > 14) ? _age - 1 : _age), onPlus: () => setState(() => _age++)), const Divider(color: Colors.grey, height: 24, thickness: 0.2), _buildStepperRow("Poids", "$_weight kg", onMinus: () => setState(() => _weight = (_weight > 30) ? _weight - 0.5 : _weight), onPlus: () => setState(() => _weight += 0.5)), const Divider(color: Colors.grey, height: 24, thickness: 0.2), _buildStepperRow("Taille", "$_height cm", onMinus: () => setState(() => _height = (_height > 100) ? _height - 1 : _height), onPlus: () => setState(() => _height++))])),
              const SizedBox(height: 24),
              _sectionTitle("PROFIL SPORTIF"),
              _buildDropdownMap("Niveau d'expérience", _levels, _selectedLevel, (val) { setState(() => _selectedLevel = val); }),
              const SizedBox(height: 16),
              _buildDropdown("Sport Principal", _sportsSpecs.keys.toList(), _selectedSport, (val) { setState(() { _selectedSport = val; _selectedSpecialty = null; }); }),
              const SizedBox(height: 16),
              if (_selectedSport != null) _buildDropdown("Spécialité", _sportsSpecs[_selectedSport]!, _selectedSpecialty, (val) { setState(() => _selectedSpecialty = val); }),
              const SizedBox(height: 40),
              _sectionTitle("CALIBRATION & PLANIFICATION"),
              InkWell(onTap: _goToLab, borderRadius: BorderRadius.circular(16), child: Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(border: Border.all(color: Colors.white24), borderRadius: BorderRadius.circular(16), color: Colors.white10), child: Row(children: [const Icon(Icons.science, color: Colors.cyanAccent, size: 30), const SizedBox(width: 16), const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text("Laboratoire de Performance", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)), Text("VMA, FTP, 1RM, Zones...", style: TextStyle(color: Colors.grey, fontSize: 12))])), const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16)]))),
              const SizedBox(height: 16),
              InkWell(onTap: _goToMatrix, borderRadius: BorderRadius.circular(16), child: Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(border: Border.all(color: Colors.white24), borderRadius: BorderRadius.circular(16), color: Colors.white10), child: Row(children: [const Icon(Icons.calendar_month, color: Colors.purpleAccent, size: 30), const SizedBox(width: 16), const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text("Semaine Type (Matrice)", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)), Text("Disponibilités, Club & Créneaux...", style: TextStyle(color: Colors.grey, fontSize: 12))])), const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16)]))),
              const SizedBox(height: 16),
              InkWell(onTap: _goToEquipment, borderRadius: BorderRadius.circular(16), child: Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(border: Border.all(color: Colors.white24), borderRadius: BorderRadius.circular(16), color: Colors.white10), child: Row(children: [const Icon(Icons.fitness_center, color: Color(0xFFFF453A), size: 30), const SizedBox(width: 16), const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text("Matériel & Santé", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)), Text("Équipements dispo & Blessures...", style: TextStyle(color: Colors.grey, fontSize: 12))])), const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16)]))),
              const SizedBox(height: 32),
              SizedBox(width: double.infinity, child: ElevatedButton(onPressed: _isSaving ? null : _submitProfile, style: ElevatedButton.styleFrom(backgroundColor: voltYellow, foregroundColor: Colors.black, padding: const EdgeInsets.symmetric(vertical: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))), child: _isSaving ? const CircularProgressIndicator(color: Colors.black) : Text("ENREGISTRER LE PROFIL", style: GoogleFonts.rubik(fontSize: 16, fontWeight: FontWeight.w900, letterSpacing: 1)))),
              const SizedBox(height: 40),
            ]),
        ),
      ),
    );
  }

  Widget _sectionTitle(String title) => Padding(padding: const EdgeInsets.only(bottom: 12), child: Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)));
  Widget _buildTextField(String label, TextEditingController controller) => TextFormField(controller: controller, style: const TextStyle(color: Colors.white), decoration: InputDecoration(labelText: label, labelStyle: const TextStyle(color: Colors.grey), filled: true, fillColor: const Color(0xFF1C1C1E), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none)), validator: (val) => val!.isEmpty ? "Requis" : null);
  Widget _buildDropdown(String label, List<String> items, String? currentValue, Function(String?) onChanged) => DropdownButtonFormField<String>(value: currentValue, dropdownColor: const Color(0xFF2C2C2E), style: const TextStyle(color: Colors.white), decoration: InputDecoration(labelText: label, labelStyle: const TextStyle(color: Colors.grey), filled: true, fillColor: const Color(0xFF1C1C1E), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none)), items: items.map((e) => DropdownMenuItem(value: e, child: Text(e, overflow: TextOverflow.ellipsis))).toList(), onChanged: onChanged, validator: (val) => val == null ? "Requis" : null);
  Widget _buildDropdownMap(String label, Map<String, String> items, String? currentValue, Function(String?) onChanged) => DropdownButtonFormField<String>(value: currentValue, isExpanded: true, dropdownColor: const Color(0xFF2C2C2E), style: const TextStyle(color: Colors.white), decoration: InputDecoration(labelText: label, labelStyle: const TextStyle(color: Colors.grey), filled: true, fillColor: const Color(0xFF1C1C1E), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none)), items: items.entries.map((e) => DropdownMenuItem(value: e.key, child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [Text(e.key, style: const TextStyle(fontWeight: FontWeight.bold)), Text(e.value, style: const TextStyle(fontSize: 10, color: Colors.grey))]))).toList(), onChanged: onChanged, validator: (val) => val == null ? "Requis" : null);
  Widget _buildStepperRow(String label, String valueDisplay, {required VoidCallback onMinus, required VoidCallback onPlus}) => Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Text(label, style: const TextStyle(color: Colors.white, fontSize: 16)), Row(children: [_circleBtn(Icons.remove, onMinus), Container(alignment: Alignment.center, width: 80, child: Text(valueDisplay, style: GoogleFonts.robotoMono(color: const Color(0xFFCCFF00), fontSize: 18, fontWeight: FontWeight.bold))), _circleBtn(Icons.add, onPlus)])]);
  Widget _circleBtn(IconData icon, VoidCallback onTap) => InkWell(onTap: onTap, borderRadius: BorderRadius.circular(20), child: Container(width: 32, height: 32, decoration: const BoxDecoration(color: Color(0xFF333333), shape: BoxShape.circle), child: Icon(icon, color: Colors.white, size: 18)));
}
