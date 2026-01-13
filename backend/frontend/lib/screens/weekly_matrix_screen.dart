import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/profile_draft.dart'; // <--- AJOUT

class WeeklyMatrixScreen extends StatefulWidget {
  const WeeklyMatrixScreen({super.key});

  @override
  State<WeeklyMatrixScreen> createState() => _WeeklyMatrixScreenState();
}

class _WeeklyMatrixScreenState extends State<WeeklyMatrixScreen> {
  // --- COLORS ---
  final Color _bgDark = const Color(0xFF000000);
  final Color _cardDark = const Color(0xFF1C1C1E);
  final Color _voltYellow = const Color(0xFFCCFF00);
  final Color _redStrength = const Color(0xFFFF453A);
  final Color _blueClub = const Color(0xFF2196F3);
  final Color _purpleLibre = const Color(0xFFA020F0);
  final Color _textGrey = const Color(0xFF8E8E93);
  // --- DATA MODEL ---
  final List<String> _days = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"];
  final List<String> _types = ["Repos", "PPS (Sport)", "PPG (Renfo)", "Libre (IA)", "Club (Fixe)"];

  late Map<String, List<Map<String, dynamic>>> _matrix;

  @override
  void initState() {
    super.initState();
    _initMatrix();
  }

  void _initMatrix() {
    _matrix = {
      for (var day in _days)
        day: [
          {'type': 'Repos', 'duration': 0.0}, 
          {'type': 'Repos', 'duration': 0.0},
        ]
    };
  }

  // --- SAVE DATA (CONNECTÉ) ---
  void _saveMatrix() {
    // On sauvegarde la matrice brute dans le Draft
    ProfileDraft().constraints['time_matrix'] = _matrix;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text("💾 Semaine type enregistrée ! L'IA va structurer le cycle."),
        backgroundColor: _voltYellow,
        behavior: SnackBarBehavior.floating,
      ),
    );
    Navigator.pop(context);
  }

  Color _getTypeColor(String type) {
    if (type.contains("PPS")) return _voltYellow;
    if (type.contains("PPG")) return _redStrength;
    if (type.contains("Club")) return _blueClub;
    if (type.contains("Libre")) return _purpleLibre;
    return _textGrey;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      appBar: AppBar(
        backgroundColor: _bgDark,
        title: Text("SEMAINE TYPE", style: GoogleFonts.bebasNeue(fontSize: 24, letterSpacing: 2, color: Colors.white)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
           IconButton(
            icon: const Icon(Icons.refresh, color: Colors.grey),
            onPressed: () => setState(() => _initMatrix()),
            tooltip: "Reset",
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            color: _bgDark,
            child: Row(
              children: [
                const Icon(Icons.info_outline, color: Colors.grey, size: 16),
                const SizedBox(width: 8),
                Expanded(child: Text("Définis tes disponibilités. L'IA comblera les créneaux 'Libre' selon ta fatigue.", style: GoogleFonts.rubik(color: Colors.grey, fontSize: 12))),
              ],
            ),
          ),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: _days.length,
              separatorBuilder: (ctx, i) => const SizedBox(height: 16),
              itemBuilder: (ctx, i) {
                return _buildDayCard(_days[i]);
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: _bgDark, border: Border(top: BorderSide(color: Colors.white.withOpacity(0.1)))),
        child: ElevatedButton(
          onPressed: _saveMatrix,
          style: ElevatedButton.styleFrom(backgroundColor: _voltYellow, foregroundColor: Colors.black, padding: const EdgeInsets.symmetric(vertical: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
          child: Text("VALIDER LA SEMAINE", style: GoogleFonts.rubik(fontWeight: FontWeight.bold, letterSpacing: 1)),
        ),
      ),
    );
  }

  Widget _buildDayCard(String day) {
    List<Map<String, dynamic>> slots = _matrix[day]!;
    bool isActiveDay = slots.any((s) => s['type'] != 'Repos');
    return Container(
      decoration: BoxDecoration(color: _cardDark, borderRadius: BorderRadius.circular(12), border: Border.all(color: isActiveDay ? Colors.white.withOpacity(0.1) : Colors.transparent)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(width: double.infinity, padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8), decoration: BoxDecoration(color: isActiveDay ? Colors.white.withOpacity(0.05) : Colors.transparent, borderRadius: const BorderRadius.vertical(top: Radius.circular(12))), child: Text(day, style: GoogleFonts.bebasNeue(fontSize: 18, letterSpacing: 1.5, color: isActiveDay ? Colors.white : _textGrey))),
          Padding(padding: const EdgeInsets.all(12), child: Column(children: [
                _buildSlotRow(day, 0, "Créneau 1 (Matin)"),
                const Divider(color: Colors.white10, height: 24),
                _buildSlotRow(day, 1, "Créneau 2 (Soir)"),
              ])),
        ]),
    );
  }

  Widget _buildSlotRow(String day, int slotIndex, String label) {
    Map<String, dynamic> slot = _matrix[day]![slotIndex];
    String currentType = slot['type'];
    double currentDuration = slot['duration'];
    bool isRest = currentType == 'Repos';
    Color typeColor = _getTypeColor(currentType);

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text(label, style: const TextStyle(color: Colors.grey, fontSize: 10)),
            Container(height: 32, padding: const EdgeInsets.symmetric(horizontal: 12), decoration: BoxDecoration(color: isRest ? Colors.transparent : typeColor.withOpacity(0.1), borderRadius: BorderRadius.circular(8), border: Border.all(color: isRest ? Colors.white24 : typeColor)),
              child: DropdownButton<String>(
                value: currentType, dropdownColor: const Color(0xFF2C2C2E), underline: const SizedBox(),
                icon: Icon(Icons.arrow_drop_down, color: isRest ? Colors.grey : typeColor, size: 18),
                style: GoogleFonts.rubik(fontSize: 12, fontWeight: FontWeight.bold, color: isRest ? Colors.grey : typeColor),
                items: _types.map((String value) { return DropdownMenuItem<String>(value: value, child: Text(value)); }).toList(),
                onChanged: (newValue) { setState(() { _matrix[day]![slotIndex]['type'] = newValue!; if (newValue == 'Repos') { _matrix[day]![slotIndex]['duration'] = 0.0; } else if (currentDuration == 0) { _matrix[day]![slotIndex]['duration'] = 60.0; } }); },
              ),
            ),
          ]),
        if (!isRest) ...[
          const SizedBox(height: 8),
          Row(children: [
              const Icon(Icons.timer_outlined, color: Colors.grey, size: 16),
              const SizedBox(width: 8),
              Expanded(child: SliderTheme(data: SliderThemeData(activeTrackColor: typeColor, inactiveTrackColor: Colors.white10, thumbColor: Colors.white, overlayColor: typeColor.withOpacity(0.2), trackHeight: 4, thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6)), child: Slider(value: currentDuration, min: 30, max: 300, divisions: 18, label: "${currentDuration.round()} min", onChanged: (val) { setState(() { _matrix[day]![slotIndex]['duration'] = val; }); }))),
              const SizedBox(width: 8),
              SizedBox(width: 60, child: Text(_formatDuration(currentDuration), textAlign: TextAlign.end, style: GoogleFonts.robotoMono(color: Colors.white, fontSize: 13))),
            ]),
        ] else ...[ const SizedBox(height: 20, child: Align(alignment: Alignment.centerLeft, child: Text("— OFF —", style: TextStyle(color: Colors.white10, fontSize: 10)))) ]
      ]);
  }

  String _formatDuration(double minutes) {
    int h = minutes ~/ 60;
    int m = (minutes % 60).toInt();
    if (h > 0) return "${h}h${m.toString().padLeft(2, '0')}";
    return "${m} min";
  }
}
