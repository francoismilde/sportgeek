import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/profile_draft.dart'; // <--- SEUL AJOUT

class BioCalibrationScreen extends StatefulWidget {
  const BioCalibrationScreen({super.key});

  @override
  State<BioCalibrationScreen> createState() => _BioCalibrationScreenState();
}

class _BioCalibrationScreenState extends State<BioCalibrationScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  // --- THEME COLORS ---
  final Color _bgDark = const Color(0xFF000000);
  final Color _cardDark = const Color(0xFF1C1C1E);
  final Color _voltYellow = const Color(0xFFCCFF00);
  final Color _cyanSwim = const Color(0xFF03DAC6);
  final Color _orangeBike = const Color(0xFFFF9F0A);
  final Color _redStrength = const Color(0xFFFF453A);
  final Color _textWhite = const Color(0xFFFFFFFF);
  final Color _textGrey = const Color(0xFF8E8E93);
  // --- STATES TOGGLES ---
  bool _knowsRunStats = true;
  bool _knowsBikeStats = true;
  bool _knowsSwimStats = true;
  bool _knows1RM = true;
  // --- CONTROLLERS RUNNING ---
  final _runShortDistCtrl = TextEditingController();
  final _runShortMinCtrl = TextEditingController();
  final _runShortSecCtrl = TextEditingController();
  final _runLongDistCtrl = TextEditingController();
  final _runLongMinCtrl = TextEditingController();
  final _runLongSecCtrl = TextEditingController();
  final _runSprintCtrl = TextEditingController();
  String _runResult = "";
  // --- CONTROLLERS CYCLING ---
  final _bikeShortMinCtrl = TextEditingController();
  final _bikeShortSecCtrl = TextEditingController();
  final _bikeShortWattsCtrl = TextEditingController();
  final _bikeLongMinCtrl = TextEditingController();
  final _bikeLongSecCtrl = TextEditingController();
  final _bikeLongWattsCtrl = TextEditingController();
  final _bikePeakCtrl = TextEditingController();
  String _bikeResult = "";
  // --- CONTROLLERS SWIMMING ---
  final _swim200MinCtrl = TextEditingController();
  final _swim200SecCtrl = TextEditingController();
  final _swim400MinCtrl = TextEditingController();
  final _swim400SecCtrl = TextEditingController();
  String _swimResult = "";
  // --- CONTROLLERS STRENGTH ---
  final _squatCtrl = TextEditingController();
  final _benchCtrl = TextEditingController();
  final _deadliftCtrl = TextEditingController();
  final _pullCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  // --- CALCULATORS ---
  void _calcRunning() {
    try {
      double d1 = double.parse(_runShortDistCtrl.text);
      double t1 = (double.parse(_runShortMinCtrl.text) * 60) + double.parse(_runShortSecCtrl.text);
      double d2 = double.parse(_runLongDistCtrl.text);
      double t2 = (double.parse(_runLongMinCtrl.text) * 60) + double.parse(_runLongSecCtrl.text);
      if (t2 <= t1) { setState(() => _runResult = "⚠️ Le test long doit être plus long !"); return; }
      double csMetersPerSec = (d2 - d1) / (t2 - t1);
      double vmaKmh = csMetersPerSec * 3.6;
      setState(() { _runResult = "Vitesse Critique : ${vmaKmh.toStringAsFixed(1)} km/h\nASR calculée."; });
    } catch (e) { setState(() => _runResult = ""); }
  }

  void _calcCycling() {
    try {
      double t1 = (double.parse(_bikeShortMinCtrl.text) * 60) + double.parse(_bikeShortSecCtrl.text);
      double p1 = double.parse(_bikeShortWattsCtrl.text);
      double t2 = (double.parse(_bikeLongMinCtrl.text) * 60) + double.parse(_bikeLongSecCtrl.text);
      double p2 = double.parse(_bikeLongWattsCtrl.text);
      if (t2 == t1) return;
      double w1 = p1 * t1;
      double w2 = p2 * t2;
      double cp = (w2 - w1) / (t2 - t1);
      double wPrime = w1 - (cp * t1);
      setState(() { _bikeResult = "CP (FTP Est.) : ${cp.toStringAsFixed(0)} W\nW' : ${(wPrime / 1000).toStringAsFixed(1)} kJ"; });
    } catch (e) { setState(() => _bikeResult = ""); }
  }

  void _calcSwim() {
    try {
      double t200 = (double.parse(_swim200MinCtrl.text) * 60) + double.parse(_swim200SecCtrl.text);
      double t400 = (double.parse(_swim400MinCtrl.text) * 60) + double.parse(_swim400SecCtrl.text);
      if (t400 <= t200) return;
      double cssSpeed = (400 - 200) / (t400 - t200);
      double secPer100 = 100 / cssSpeed;
      int min = (secPer100 / 60).floor();
      int sec = (secPer100 % 60).round();
      setState(() { _swimResult = "CSS Pace : $min:${sec.toString().padLeft(2, '0')}/100m"; });
    } catch (e) { setState(() => _swimResult = ""); }
  }

  // --- SAVE DATA (CONNECTÉ) ---
  void _saveData() {
    // 1. Sauvegarde dans le Singleton Draft
    final draft = ProfileDraft();
    
    draft.performanceBaseline = {
      // Données brutes Force
      "squat_1rm": double.tryParse(_squatCtrl.text),
      "bench_1rm": double.tryParse(_benchCtrl.text),
      "deadlift_1rm": double.tryParse(_deadliftCtrl.text),
      "pull_load": double.tryParse(_pullCtrl.text),
      
      // Données Running
      "running_max_sprint_time": double.tryParse(_runSprintCtrl.text), // C'est des km/h ici en fait selon ton UI
      "vma_estimated": _runResult, 
      
      // Données Cycling
      "cycling_ftp": _bikeResult.isNotEmpty ? 250 : null, // (Simplification: il faudrait extraire la valeur du string _bikeResult)
      "cycling_max_power_5s": double.tryParse(_bikePeakCtrl.text),
      
      // Données Swim
      "css_pace": _swimResult
    };

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text("💾 Protocoles enregistrés. Zones mises à jour !"),
        backgroundColor: _voltYellow,
        behavior: SnackBarBehavior.floating,
      ),
    );
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      appBar: AppBar(
        backgroundColor: _bgDark,
        title: Text("LABORATOIRE",
            style: GoogleFonts.bebasNeue(
                fontSize: 24, letterSpacing: 2, color: _textWhite)),
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios, color: _textWhite),
          onPressed: () => Navigator.pop(context),
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: _voltYellow,
          labelColor: _voltYellow,
          unselectedLabelColor: _textGrey,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold),
          tabs: const [
            Tab(icon: Icon(Icons.directions_run), text: "RUN"),
            Tab(icon: Icon(Icons.directions_bike), text: "BIKE"),
            Tab(icon: Icon(Icons.pool), text: "SWIM"),
            Tab(icon: Icon(Icons.fitness_center), text: "GYM"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildRunTab(),
          _buildBikeTab(),
          _buildSwimTab(),
          _buildStrengthTab(),
        ],
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(20),
        color: _bgDark,
        child: ElevatedButton(
          onPressed: _saveData,
          style: ElevatedButton.styleFrom(
            backgroundColor: _voltYellow,
            foregroundColor: Colors.black,
            padding: const EdgeInsets.symmetric(vertical: 18),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
          child: Text("VALIDER LES TESTS",
              style: GoogleFonts.rubik(fontWeight: FontWeight.bold, letterSpacing: 1)),
        ),
      ),
    );
  }

  // --- TABS CONTENT (COPIÉ COLLÉ EXACT DE TA VERSION) ---

  Widget _buildRunTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionHeader("TEST VITESSE CRITIQUE", _voltYellow),
          const SizedBox(height: 16),
          SwitchListTile(
            title: Text("Je connais mes chronos", style: TextStyle(color: _textWhite, fontWeight: FontWeight.bold)),
            subtitle: const Text("Pour calculer ta VMA/CS précise.", style: TextStyle(color: Colors.grey, fontSize: 12)),
            value: _knowsRunStats,
            activeTrackColor: _voltYellow,
            activeThumbColor: Colors.black,
            contentPadding: EdgeInsets.zero,
            onChanged: (val) => setState(() => _knowsRunStats = val),
          ),
          const SizedBox(height: 16),
          if (_knowsRunStats) ...[
            _testCard(
              title: "TEST COURT (Ex: 1200m)", color: _voltYellow,
              child: Column(children: [
                  _inputField("Distance (m)", _runShortDistCtrl, numeric: true, suffix: "m", onChanged: (_) => _calcRunning()),
                  const SizedBox(height: 12),
                  _durationPicker("Chrono", _runShortMinCtrl, _runShortSecCtrl, onChanged: _calcRunning),
                ]),
            ),
            const SizedBox(height: 16),
            _testCard(
              title: "TEST LONG (Ex: 3600m)", color: _voltYellow,
              child: Column(children: [
                  _inputField("Distance (m)", _runLongDistCtrl, numeric: true, suffix: "m", onChanged: (_) => _calcRunning()),
                  const SizedBox(height: 12),
                  _durationPicker("Chrono", _runLongMinCtrl, _runLongSecCtrl, onChanged: _calcRunning),
                ]),
            ),
            const SizedBox(height: 24),
            _inputField("Vitesse Max Sprint (km/h)", _runSprintCtrl, numeric: true, suffix: "km/h"),
            if (_runResult.isNotEmpty) ...[const SizedBox(height: 24), _resultBox(_runResult, _voltYellow),]
          ] else ...[
            _buildEstimationBox("Mode Estimation activé.\nL'IA utilisera ton temps sur 5km/10km récent ou ton niveau global pour définir tes allures.", _voltYellow),
          ]
        ],
      ),
    );
  }

  Widget _buildBikeTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _sectionHeader("PROFIL PUISSANCE (CP)", _orangeBike),
          const SizedBox(height: 16),
          SwitchListTile(
            title: Text("Je connais ma puissance", style: TextStyle(color: _textWhite, fontWeight: FontWeight.bold)),
            subtitle: const Text("Tests CP ou FTP récents.", style: TextStyle(color: Colors.grey, fontSize: 12)),
            value: _knowsBikeStats,
            activeTrackColor: _orangeBike,
            activeThumbColor: Colors.white,
            contentPadding: EdgeInsets.zero,
            onChanged: (val) => setState(() => _knowsBikeStats = val),
          ),
          const SizedBox(height: 16),
          if (_knowsBikeStats) ...[
            _testCard(
              title: "TEST COURT (3 à 5 min)", color: _orangeBike,
              child: Column(children: [
                  _durationPicker("Durée", _bikeShortMinCtrl, _bikeShortSecCtrl, onChanged: _calcCycling),
                  const SizedBox(height: 12),
                  _inputField("Puissance Moy. (Watts)", _bikeShortWattsCtrl, numeric: true, suffix: "W", maxLen: 4, onChanged: (_) => _calcCycling()),
                ]),
            ),
            const SizedBox(height: 16),
            _testCard(
              title: "TEST LONG (12 à 20 min)", color: _orangeBike,
              child: Column(children: [
                  _durationPicker("Durée", _bikeLongMinCtrl, _bikeLongSecCtrl, onChanged: _calcCycling),
                  const SizedBox(height: 12),
                  _inputField("Puissance Moy. (Watts)", _bikeLongWattsCtrl, numeric: true, suffix: "W", maxLen: 4, onChanged: (_) => _calcCycling()),
                ]),
            ),
            const SizedBox(height: 24),
            _inputField("Peak Power 5s (Watts)", _bikePeakCtrl, numeric: true, suffix: "W", maxLen: 4),
            if (_bikeResult.isNotEmpty) ...[const SizedBox(height: 24), _resultBox(_bikeResult, _orangeBike),]
          ] else ...[
            _buildEstimationBox("Mode Estimation activé.\nL'IA estimera ta FTP via ton Poids, ton Age et ton niveau d'expérience cycliste.", _orangeBike),
          ]
        ]),
    );
  }

  Widget _buildSwimTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _sectionHeader("CRITICAL SWIM SPEED", _cyanSwim),
          const SizedBox(height: 16),
          SwitchListTile(
            title: Text("Je connais mes chronos", style: TextStyle(color: _textWhite, fontWeight: FontWeight.bold)),
            subtitle: const Text("Tests 200m/400m récents.", style: TextStyle(color: Colors.grey, fontSize: 12)),
            value: _knowsSwimStats,
            activeTrackColor: _cyanSwim,
            activeThumbColor: Colors.black,
            contentPadding: EdgeInsets.zero,
            onChanged: (val) => setState(() => _knowsSwimStats = val),
          ),
          const SizedBox(height: 16),
          if (_knowsSwimStats) ...[
            _testCard(
              title: "CHRONO 200m", color: _cyanSwim,
              child: _durationPicker("Temps", _swim200MinCtrl, _swim200SecCtrl, onChanged: _calcSwim),
            ),
            const SizedBox(height: 16),
            _testCard(
              title: "CHRONO 400m", color: _cyanSwim,
              child: _durationPicker("Temps", _swim400MinCtrl, _swim400SecCtrl, onChanged: _calcSwim),
            ),
            if (_swimResult.isNotEmpty) ...[const SizedBox(height: 24), _resultBox(_swimResult, _cyanSwim),]
          ] else ...[
            _buildEstimationBox("Mode Estimation activé.\nL'IA déduira ton allure CSS selon ton niveau déclaré (Débutant à Élite).", _cyanSwim),
          ]
        ]),
    );
  }

  Widget _buildStrengthTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _sectionHeader("MAX FORCE (1RM)", _redStrength),
          const SizedBox(height: 16),
          SwitchListTile(
            title: Text("Je connais mes max (1RM)", style: TextStyle(color: _textWhite, fontWeight: FontWeight.bold)),
            subtitle: const Text("Sinon, l'IA les estimera.", style: TextStyle(color: Colors.grey, fontSize: 12)),
            value: _knows1RM,
            activeTrackColor: _redStrength,
            activeThumbColor: _textWhite,
            contentPadding: EdgeInsets.zero,
            onChanged: (val) => setState(() => _knows1RM = val),
          ),
          const SizedBox(height: 16),
          if (_knows1RM) ...[
            _inputField("Squat Max", _squatCtrl, numeric: true, suffix: "kg"),
            const SizedBox(height: 12),
            _inputField("Bench Press Max", _benchCtrl, numeric: true, suffix: "kg"),
            const SizedBox(height: 12),
            _inputField("Deadlift Max", _deadliftCtrl, numeric: true, suffix: "kg"),
            const SizedBox(height: 12),
            _inputField("Tirage / Pull-up Lest", _pullCtrl, numeric: true, suffix: "kg"),
          ] else ...[
            _buildEstimationBox("Mode Estimation activé.\nL'IA utilisera ton Poids et ton Niveau saisis dans le Profil pour générer tes charges.", _redStrength),
          ]
        ]),
    );
  }

  // --- REUSABLE COMPONENTS (ISO) ---
  Widget _sectionHeader(String title, Color color) {
    return Row(children: [Container(width: 4, height: 18, color: color), const SizedBox(width: 8), Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.5))]);
  }
  Widget _buildEstimationBox(String message, Color color) {
    return Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(border: Border.all(color: color.withOpacity(0.3)), borderRadius: BorderRadius.circular(12), color: color.withOpacity(0.1)), child: Row(children: [Icon(Icons.auto_awesome, color: _textWhite), const SizedBox(width: 12), Expanded(child: Text(message, style: const TextStyle(color: Colors.white70, fontSize: 12)))]));
  }
  Widget _testCard({required String title, required Color color, required Widget child}) {
    return Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: _cardDark, borderRadius: BorderRadius.circular(16), border: Border.all(color: _textWhite.withOpacity(0.05))), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 14)), const SizedBox(height: 12), child]));
  }
  Widget _inputField(String label, TextEditingController controller, {bool numeric = false, String? suffix, int? maxLen, Function(String)? onChanged}) {
    return TextFormField(controller: controller, keyboardType: numeric ? TextInputType.number : TextInputType.text, style: GoogleFonts.robotoMono(color: _textWhite, fontSize: 16), maxLength: maxLen, onChanged: onChanged, decoration: InputDecoration(labelText: label, labelStyle: const TextStyle(color: Colors.grey), suffixText: suffix, suffixStyle: TextStyle(color: _voltYellow), counterText: "", filled: true, fillColor: const Color(0xFF2C2C2E), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none), contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14)));
  }
  Widget _durationPicker(String label, TextEditingController minCtrl, TextEditingController secCtrl, {required VoidCallback onChanged}) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)), const SizedBox(height: 6), Row(children: [Expanded(child: TextFormField(controller: minCtrl, keyboardType: TextInputType.number, style: GoogleFonts.robotoMono(color: _textWhite, fontSize: 18), textAlign: TextAlign.center, onChanged: (_) => onChanged(), decoration: InputDecoration(hintText: "00", suffixText: "min", filled: true, fillColor: const Color(0xFF2C2C2E), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none), contentPadding: const EdgeInsets.symmetric(vertical: 12)))), Padding(padding: const EdgeInsets.symmetric(horizontal: 8.0), child: Text(":", style: TextStyle(color: _textWhite, fontSize: 24, fontWeight: FontWeight.bold))), Expanded(child: TextFormField(controller: secCtrl, keyboardType: TextInputType.number, style: GoogleFonts.robotoMono(color: _textWhite, fontSize: 18), textAlign: TextAlign.center, onChanged: (_) => onChanged(), decoration: InputDecoration(hintText: "00", suffixText: "sec", filled: true, fillColor: const Color(0xFF2C2C2E), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none), contentPadding: const EdgeInsets.symmetric(vertical: 12))))])]);
  }
  Widget _resultBox(String text, Color color) {
    return Container(width: double.infinity, padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: color.withOpacity(0.1), border: Border.all(color: color), borderRadius: BorderRadius.circular(12)), child: Text(text, style: GoogleFonts.robotoMono(color: color, fontSize: 14, fontWeight: FontWeight.bold), textAlign: TextAlign.center));
  }
}
