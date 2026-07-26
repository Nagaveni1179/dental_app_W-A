import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'dentist_dashboard.dart';
import 'dentist_patients.dart';
import 'dentist_consultations.dart';
import 'dentist_appointments.dart';
import 'dentist_profile.dart';

class DentistHome extends StatefulWidget {
  const DentistHome({super.key});

  @override
  State<DentistHome> createState() => _DentistHomeState();
}

class _DentistHomeState extends State<DentistHome> {
  int _index = 0;

  final List<Widget> _pages = const [
    DentistDashboard(),
    DentistPatients(),
    DentistConsultations(),
    DentistAppointments(),
    DentistProfile(),
  ];

  final List<_NavItem> _items = const [
    _NavItem('Home', Icons.dashboard_outlined, Icons.dashboard_rounded),
    _NavItem('Patients', Icons.people_outline, Icons.people_rounded),
    _NavItem('Consults', Icons.forum_outlined, Icons.forum_rounded),
    _NavItem('Visits', Icons.event_outlined, Icons.event_rounded),
    _NavItem('Profile', Icons.person_outline, Icons.person_rounded),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: IndexedStack(index: _index, children: _pages),
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
