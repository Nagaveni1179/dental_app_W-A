import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'admin_dashboard.dart';
import 'admin_users.dart';
import 'admin_reports.dart';
import 'admin_profile.dart';

class AdminHome extends StatefulWidget {
  const AdminHome({super.key});

  @override
  State<AdminHome> createState() => _AdminHomeState();
}

class _AdminHomeState extends State<AdminHome> {
  int _index = 0;

  final List<Widget> _pages = const [
    AdminDashboard(),
    AdminUsers(),
    AdminReports(),
    AdminProfile(),
  ];

  final List<_NavItem> _items = const [
    _NavItem('Home', Icons.dashboard_outlined, Icons.dashboard_rounded),
    _NavItem('Users', Icons.group_outlined, Icons.group_rounded),
    _NavItem('Reports', Icons.bar_chart_outlined, Icons.bar_chart_rounded),
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
