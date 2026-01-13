import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'profile_setup_screen.dart';
import 'bio_calibration_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  final Color _bgDark = const Color(0xFF000000);
  final Color _cardDark = const Color(0xFF1C1C1E);
  final Color _voltYellow = const Color(0xFFCCFF00);
  final Color _purpleAI = const Color(0xFFA020F0);
  final Color _textWhite = const Color(0xFFFFFFFF);
  final Color _textGrey = const Color(0xFF8E8E93);
  final Color _successGreen = const Color(0xFF32D74B);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgDark,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(context),
              const SizedBox(height: 24),
              _buildHeroCard(context),
              const SizedBox(height: 24),
              const Text(
                "COCKPIT INSIGHT",
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFF8E8E93), letterSpacing: 1.0),
              ),
              const SizedBox(height: 12),
              _buildCoachWidget(),
              const SizedBox(height: 24),
              _buildTimelineSection(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        InkWell(
          onTap: () {
            Navigator.push(context, MaterialPageRoute(builder: (context) => const ProfileSetupScreen()));
          },
          borderRadius: BorderRadius.circular(30),
          child: Row(
            children: [
              Container(
                width: 44, height: 44,
                decoration: BoxDecoration(shape: BoxShape.circle, gradient: const LinearGradient(colors: [Color(0xFF333333), Color(0xFF555555)], begin: Alignment.topLeft, end: Alignment.bottomRight), border: Border.all(color: _voltYellow, width: 2)),
                child: Icon(Icons.person, color: _textWhite, size: 24),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Alexandre", style: GoogleFonts.rubik(fontSize: 16, fontWeight: FontWeight.w700, color: _textWhite)),
                  Text("ELITE SQUAD", style: GoogleFonts.rubik(fontSize: 12, fontWeight: FontWeight.w800, color: _voltYellow, letterSpacing: 1.0)),
                ],
              ),
            ],
          ),
        ),
        InkWell(
          onTap: () {
            Navigator.push(context, MaterialPageRoute(builder: (context) => const BioCalibrationScreen()));
          },
          borderRadius: BorderRadius.circular(20),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(color: _successGreen.withOpacity(0.1), borderRadius: BorderRadius.circular(20), border: Border.all(color: _successGreen)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text("92%", style: GoogleFonts.rubik(fontSize: 14, fontWeight: FontWeight.bold, color: _successGreen)),
                Text("READINESS (LAB)", style: GoogleFonts.rubik(fontSize: 8, fontWeight: FontWeight.bold, color: _successGreen.withOpacity(0.8))),
              ],
            ),
          ),
        )
      ],
    );
  }

  Widget _buildHeroCard(BuildContext context) {
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(minHeight: 280),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: _cardDark, borderRadius: BorderRadius.circular(24), border: Border.all(color: const Color(0xFF333333)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 30, offset: const Offset(0, 10))],
      ),
      child: Stack(
        children: [
          Positioned(right: -20, top: -20, child: Icon(Icons.flash_on, size: 150, color: Colors.white.withOpacity(0.05))),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(color: const Color(0xFF333333), borderRadius: BorderRadius.circular(8)),
                    child: Text("RUNNING • INTERVALLE", style: GoogleFonts.rubik(fontSize: 12, fontWeight: FontWeight.w600, color: _textWhite)),
                  ),
                  const Text("🔥", style: TextStyle(fontSize: 20)),
                ],
              ),
              const SizedBox(height: 15),
              Text("VMA\nPYRAMIDALE", style: GoogleFonts.rubik(fontSize: 28, fontWeight: FontWeight.w900, color: _textWhite, height: 1.1)),
              const SizedBox(height: 20),
              Row(children: [_buildMetric("55'", "Durée"), const SizedBox(width: 20), _buildMetric("110", "TSS"), const SizedBox(width: 20), _buildMetric("High", "Intensité")]),
              const SizedBox(height: 30),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () { ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("🚀 Lancement du Module 5..."))); },
                  style: ElevatedButton.styleFrom(backgroundColor: _voltYellow, foregroundColor: Colors.black, padding: const EdgeInsets.symmetric(vertical: 18), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), elevation: 10, shadowColor: _voltYellow.withOpacity(0.3)),
                  child: Text("DÉMARRER LA SÉANCE", style: GoogleFonts.rubik(fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1.0)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMetric(String value, String label) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(value, style: GoogleFonts.robotoMono(fontSize: 18, fontWeight: FontWeight.bold, color: _voltYellow)), Text(label, style: TextStyle(fontSize: 12, color: _textGrey))]);
  }

  // [CORRECTION] Ajustement des paddings et suppression de l'IntrinsicHeight strict qui cause l'overflow
  Widget _buildCoachWidget() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFF1C1C1E), Color(0xFF2C2C2E)], begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.transparent),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start, // Alignement en haut pour éviter le stretch forcé
        children: [
          Container(
            width: 4,
            height: 40, // Hauteur fixe pour la barre décorative au lieu de IntrinsicHeight
            decoration: BoxDecoration(color: _purpleAI, borderRadius: BorderRadius.circular(2)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("✦ ANALYSE EN COURS...", style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: _purpleAI)),
                const SizedBox(height: 6), // Réduit de 8 à 6
                Container(height: 12, width: double.infinity, decoration: BoxDecoration(color: const Color(0xFF333333), borderRadius: BorderRadius.circular(4))),
                const SizedBox(height: 6), // Réduit de 6 à 6
                Container(height: 12, width: 150, decoration: BoxDecoration(color: const Color(0xFF333333), borderRadius: BorderRadius.circular(4))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTimelineSection() {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text("CETTE SEMAINE", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: _textGrey, letterSpacing: 1.0)),
        const SizedBox(height: 12),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            _buildDayItem("L", "✔", state: "done"), _buildDayItem("M", "✔", state: "done"), _buildDayItem("M", "14", state: "active"),
            _buildDayItem("J", "15", state: "future"), _buildDayItem("V", "16", state: "future"), _buildDayItem("S", "17", state: "future"), _buildDayItem("D", "18", state: "future"),
          ]),
        const SizedBox(height: 20),
      ]);
  }

  Widget _buildDayItem(String dayName, String content, {required String state}) {
    Color circleColor; Color textColor; Color borderColor;
    if (state == "done") { circleColor = const Color(0xFF333333); textColor = _textGrey; borderColor = Colors.transparent; }
    else if (state == "active") { circleColor = _voltYellow.withOpacity(0.1); textColor = _voltYellow; borderColor = _voltYellow; }
    else { circleColor = const Color(0xFF222222); textColor = _textWhite; borderColor = const Color(0xFF333333); }
    return Column(children: [
        Text(dayName, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: state == "future" ? _textGrey : _textWhite)),
        const SizedBox(height: 6),
        Container(width: 36, height: 36, decoration: BoxDecoration(color: circleColor, shape: BoxShape.circle, border: Border.all(color: borderColor, width: 2)), child: Center(child: Text(content, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: textColor, decoration: state == "done" ? TextDecoration.lineThrough : null)))),
      ]);
  }
}
