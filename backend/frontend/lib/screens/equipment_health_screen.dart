import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/profile_draft.dart'; // <--- AJOUT

class EquipmentHealthScreen extends StatefulWidget {
  const EquipmentHealthScreen({super.key});
  @override
  State<EquipmentHealthScreen> createState() => _EquipmentHealthScreenState();
}

class _EquipmentHealthScreenState extends State<EquipmentHealthScreen> {
  // --- CONSTANTES ---
  final List<String> _equipmentList = [
    "Salle de sport commerciale (Accès total)", "Home Gym complet (Rack + Barre + Banc)", "Box de CrossFit",
    "Haltères (Dumbbells)", "Barre Olympique + Disques", "Kettlebells", "Barre de traction", "Banc de musculation", "Station à Dips / Chaise romaine",
    "Élastiques / Bandes de résistance", "Anneaux de gymnastique / TRX", "Corde à sauter", "Gilet lesté", "Médecine Ball / Wall Ball",
    "Vélo de route / VTT (Extérieur)", "Home Trainer / Zwift", "Rameur (Ergo)", "Tapis de course", "Vélo Elliptique / Assault Bike", "Piscine / Bassin"
  ];
  final List<String> _injuryZones = [
    "Cervicales / Cou", "Épaule (Coiffe des rotateurs)", "Coude / Avant-bras", "Poignet / Main", "Dos (Haut / Trapèzes)",
    "Lombaires (Bas du dos)", "Hanche / Psoas", "Adducteurs / Aine", "Ischios-jambiers", "Quadriceps",
    "Genou (Ménisque/Ligaments)", "Rotule / Tendon rotulien", "Mollet / Achille", "Cheville", "Pied / Voûte plantaire"
  ];
  final List<String> _injuryTypes = [
    "Douleur active (Aiguë)", "Gêne / Inconfort léger", "Raideur / Manque de mobilité", "Tendinite / Tendinopathie",
    "Entorse en guérison", "Déchirure musculaire (Réhab)", "Post-Opératoire (< 6 mois)", "Fragilité chronique (Prévention)"
  ];
  // --- STATE ---
  final List<String> _selectedEquipment = [];
  final List<Map<String, String?>> _declaredInjuries = [];
  // --- COLORS ---
  final Color _bgDark = const Color(0xFF000000);
  final Color _cardDark = const Color(0xFF1C1C1E);
  final Color _voltYellow = const Color(0xFFCCFF00);
  final Color _redAlert = const Color(0xFFFF453A);

  @override
  void initState() {
    super.initState();
    _selectedEquipment.add("Salle de sport commerciale (Accès total)");
  }

  void _addInjury() => setState(() => _declaredInjuries.add({'zone': null, 'type': null}));
  void _removeInjury(int index) => setState(() => _declaredInjuries.removeAt(index));

  // --- SAVE DATA (CONNECTÉ) ---
  void _saveData() {
    bool injuriesComplete = _declaredInjuries.every((inj) => inj['zone'] != null && inj['type'] != null);
    if (!injuriesComplete) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("⚠️ Complète toutes les infos blessures."), backgroundColor: Colors.orange));
      return;
    }

    // Sauvegarde Draft
    ProfileDraft().equipment = _selectedEquipment;
    ProfileDraft().injuryPrevention = {'injuries': _declaredInjuries};

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("💾 Inventaire : ${_selectedEquipment.length} items. Blessures : ${_declaredInjuries.length}."),
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
      appBar: AppBar(backgroundColor: _bgDark, title: Text("MATÉRIEL & SANTÉ", style: GoogleFonts.bebasNeue(fontSize: 24, letterSpacing: 2, color: Colors.white)), leading: IconButton(icon: const Icon(Icons.arrow_back_ios, color: Colors.white), onPressed: () => Navigator.pop(context))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _sectionHeader("ARMURERIE (ÉQUIPEMENTS)", Icons.fitness_center),
            const SizedBox(height: 12),
            Container(width: double.infinity, padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: _cardDark, borderRadius: BorderRadius.circular(16)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text("Sélectionne tout ce dont tu disposes :", style: TextStyle(color: Colors.grey, fontSize: 12)),
                  const SizedBox(height: 16),
                  Wrap(spacing: 8.0, runSpacing: 8.0, children: _equipmentList.map((equip) {
                      final isSelected = _selectedEquipment.contains(equip);
                      return FilterChip(
                        label: Text(equip), selected: isSelected,
                        onSelected: (bool selected) { setState(() { if (selected) { _selectedEquipment.add(equip); } else { _selectedEquipment.remove(equip); } }); },
                        backgroundColor: const Color(0xFF2C2C2E), selectedColor: _voltYellow, checkmarkColor: Colors.black,
                        labelStyle: TextStyle(color: isSelected ? Colors.black : Colors.white, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal, fontSize: 12),
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8), side: BorderSide(color: isSelected ? _voltYellow : Colors.transparent)), showCheckmark: false,
                      );
                    }).toList()),
                ]),
            ),
            const SizedBox(height: 32),
            _sectionHeader("INFIRMERIE (BLESSURES)", Icons.local_hospital),
            const SizedBox(height: 12),
            Container(width: double.infinity, padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: _cardDark, borderRadius: BorderRadius.circular(16), border: Border.all(color: _redAlert.withOpacity(0.1))),
              child: Column(children: [
                  if (_declaredInjuries.isEmpty) Padding(padding: const EdgeInsets.symmetric(vertical: 20), child: Column(children: [Icon(Icons.check_circle_outline, color: Colors.greenAccent.withOpacity(0.5), size: 40), const SizedBox(height: 8), const Text("Aucune blessure signalée.\nMachine opérationnelle à 100%.", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey, fontSize: 12))]))
                  else ListView.separated(shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), itemCount: _declaredInjuries.length, separatorBuilder: (ctx, i) => const Divider(color: Colors.white10, height: 24, thickness: 1), itemBuilder: (ctx, i) => _buildInjuryRow(i)),
                  const SizedBox(height: 16),
                  OutlinedButton.icon(onPressed: _addInjury, icon: Icon(Icons.add, color: _redAlert), label: Text("DÉCLARER UNE BLESSURE", style: TextStyle(color: _redAlert)), style: OutlinedButton.styleFrom(side: BorderSide(color: _redAlert.withOpacity(0.5)), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)))),
                ]),
            ),
          ]),
      ),
      bottomNavigationBar: Container(padding: const EdgeInsets.all(20), decoration: BoxDecoration(color: _bgDark, border: Border(top: BorderSide(color: Colors.white.withOpacity(0.1)))), child: ElevatedButton(onPressed: _saveData, style: ElevatedButton.styleFrom(backgroundColor: _voltYellow, foregroundColor: Colors.black, padding: const EdgeInsets.symmetric(vertical: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))), child: Text("VALIDER MATÉRIEL & SANTÉ", style: GoogleFonts.rubik(fontWeight: FontWeight.bold, letterSpacing: 1)))),
    );
  }

  Widget _sectionHeader(String title, IconData icon) => Row(children: [Icon(icon, color: Colors.grey, size: 18), const SizedBox(width: 8), Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.5))]);
  Widget _buildInjuryRow(int index) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Text("Blessure #${index + 1}", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)), IconButton(icon: const Icon(Icons.delete_outline, color: Colors.grey), onPressed: () => _removeInjury(index), padding: EdgeInsets.zero, constraints: const BoxConstraints())]),
        const SizedBox(height: 12),
        _buildDropdownMap("Zone touchée", _injuryZones, _declaredInjuries[index]['zone'], (val) => setState(() => _declaredInjuries[index]['zone'] = val)),
        const SizedBox(height: 12),
        _buildDropdownMap("Type de problème", _injuryTypes, _declaredInjuries[index]['type'], (val) => setState(() => _declaredInjuries[index]['type'] = val)),
      ]);
  }
  Widget _buildDropdownMap(String label, List<String> items, String? currentValue, Function(String?) onChanged) {
    return DropdownButtonFormField<String>(value: currentValue, isExpanded: true, dropdownColor: const Color(0xFF2C2C2E), style: const TextStyle(color: Colors.white, fontSize: 13), decoration: InputDecoration(labelText: label, labelStyle: const TextStyle(color: Colors.grey, fontSize: 12), filled: true, fillColor: const Color(0xFF2C2C2E), border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none), contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12)), items: items.map((e) => DropdownMenuItem(value: e, child: Text(e, overflow: TextOverflow.ellipsis))).toList(), onChanged: onChanged);
  }
}
