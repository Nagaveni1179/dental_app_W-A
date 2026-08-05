import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'home_tab.dart';
import 'scan_screen.dart';
import 'pain_screen.dart';
import 'appointments_screen.dart';
import 'profile_screen.dart';

class PatientHome extends StatefulWidget {
  const PatientHome({super.key});

  @override
  State<PatientHome> createState() => _PatientHomeState();
}

class _PatientHomeState extends State<PatientHome> {
  int _index = 0;

  final List<Widget> _pages = const [
    HomeTab(),
    ScanScreen(),
    PainScreen(),
    AppointmentsScreen(),
    ProfileScreen(),
  ];

  final List<_NavItem> _items = const [
    _NavItem('Home', Icons.home_outlined, Icons.home_rounded),
    _NavItem('Scan', Icons.camera_alt_outlined, Icons.camera_alt_rounded),
    _NavItem('Pain', Icons.healing_outlined, Icons.healing_rounded),
    _NavItem('Visits', Icons.event_outlined, Icons.event_rounded),
    _NavItem('Profile', Icons.person_outline, Icons.person_rounded),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: _pages[_index],
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: kCard,
          border: Border(top: BorderSide(color: kBorder)),
          boxShadow: [
            BoxShadow(
                color: Color(0x0F0F2C33), blurRadius: 12, offset: Offset(0, -2))
          ],
        ),
        child: SafeArea(
          top: false,
          child: Row(
            children: List.generate(_items.length, (i) {
              final selected = _index == i;
              final item = _items[i];
              return Expanded(
                child: InkWell(
                  onTap: () => setState(() => _index = i),
                  borderRadius: BorderRadius.circular(14),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(selected ? item.activeIcon : item.icon,
                            color: selected ? kPrimary : kTextLight, size: 24),
                        const SizedBox(height: 4),
                        Text(item.label,
                            style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: selected
                                    ? FontWeight.w700
                                    : FontWeight.w500,
                                color: selected ? kPrimary : kTextLight)),
                      ],
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  final String label;
  final IconData icon;
  final IconData activeIcon;
  const _NavItem(this.label, this.icon, this.activeIcon);
}
