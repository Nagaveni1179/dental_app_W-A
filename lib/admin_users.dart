import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';

class AdminUsers extends StatefulWidget {
  const AdminUsers({super.key});

  @override
  State<AdminUsers> createState() => _AdminUsersState();
}

class _AdminUsersState extends State<AdminUsers> {
  int _tab = 0; // 0 = patients, 1 = dentists
  late Future<List<dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getUsers(role: 'patient');
  }

  void _load() {
    setState(() {
      _future = ApiService.getUsers(role: _tab == 0 ? 'patient' : 'dentist');
    });
  }

  Future<void> _delete(int id) async {
    await ApiService.deleteUser(id);
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg,
        elevation: 0,
        foregroundColor: kText,
        centerTitle: false,
        title: const Text('Manage Users', style: kH2),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                  color: kCard,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: kBorder)),
              child: Row(
                children: [
                  _segment('Patients', 0),
                  _segment('Dentists', 1),
                ],
              ),
            ),
          ),
          Expanded(
            child: FutureBuilder<List<dynamic>>(
              future: _future,
              builder: (context, snap) {
                if (snap.connectionState == ConnectionState.waiting) {
                  return const Center(
                      child: CircularProgressIndicator(color: kPrimary));
                }
                final list = snap.data ?? [];
                if (list.isEmpty) {
                  return const Center(child: Text('No users', style: kSub));
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                  itemCount: list.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (_, i) {
                    final u = list[i] as Map<String, dynamic>;
                    return Container(
                      padding: const EdgeInsets.all(14),
                      decoration: kCardDeco,
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 22,
                            backgroundColor: kPrimary.withOpacity(0.12),
                            child: Text(
                                (u['name'] ?? '?').toString().isNotEmpty
                                    ? u['name'][0]
                                    : '?',
                                style: const TextStyle(
                                    color: kPrimary,
                                    fontWeight: FontWeight.w700)),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(u['name'] ?? '',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        color: kText,
                                        fontSize: 15)),
                                const SizedBox(height: 2),
                                Text(u['email'] ?? '', style: kSub),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline,
                                color: kDanger, size: 20),
                            onPressed: () => _confirmDelete(u['id']),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  void _confirmDelete(int id) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Remove user?'),
        content: const Text('This will permanently delete the account.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _delete(id);
            },
            child: const Text('Delete', style: TextStyle(color: kDanger)),
          ),
        ],
      ),
    );
  }

  Widget _segment(String label, int value) {
    final selected = _tab == value;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          setState(() => _tab = value);
          _load();
        },
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: selected ? kPrimary : Colors.transparent,
            borderRadius: BorderRadius.circular(9),
          ),
          child: Text(label,
              style: TextStyle(
                  color: selected ? Colors.white : kTextLight,
                  fontWeight: FontWeight.w700,
                  fontSize: 13.5)),
        ),
      ),
    );
  }
}
