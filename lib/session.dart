// Static session/auth state held in memory across screens.
class Session {
  static int userId = 0;
  static String name = '';
  static String email = '';
  static String role = 'patient'; // patient | dentist | admin
  static String phone = '';
  static int age = 0;
  static String gender = '';

  static void setUser({
    required int id,
    required String userName,
    required String userEmail,
    required String userRole,
    String userPhone = '',
    int userAge = 0,
    String userGender = '',
  }) {
    userId = id;
    name = userName;
    email = userEmail;
    role = userRole;
    phone = userPhone;
    age = userAge;
    gender = userGender;
  }

  static void clear() {
    userId = 0;
    name = '';
    email = '';
    role = 'patient';
    phone = '';
    age = 0;
    gender = '';
  }
}
