import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiService {
  // Singleton pattern
  static final ApiService instance = ApiService._internal();
  ApiService._internal();

  // Primary: 127.0.0.1 (via adb reverse tcp:8000 tcp:8000)
  // Secondary: 10.255.129.130 (Host Wi-Fi LAN IP)
  static final List<String> candidateUrls = [
    'http://127.0.0.1:8000/api',
    'http://10.255.129.130:8000/api',
    'http://localhost:8000/api',
  ];
  static String baseUrl = 'http://127.0.0.1:8000/api';
  
  String? token;
  String? currentUserId;
  String? currentUserName;
  String currentCity = 'Chennai';

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Bearer $token',
  };

  // Helper method for resilient HTTP GET
  Future<http.Response> _get(String endpoint) async {
    for (final base in candidateUrls) {
      try {
        final res = await http
            .get(Uri.parse('$base$endpoint'), headers: _headers)
            .timeout(const Duration(seconds: 4));
        if (res.statusCode >= 200 && res.statusCode < 500) {
          baseUrl = base;
          return res;
        }
      } catch (_) {}
    }
    throw Exception('Failed to connect to Kalisi API');
  }

  // Helper method for resilient HTTP POST
  Future<http.Response> _post(String endpoint, Map<String, dynamic> body) async {
    for (final base in candidateUrls) {
      try {
        final res = await http
            .post(
              Uri.parse('$base$endpoint'),
              headers: _headers,
              body: jsonEncode(body),
            )
            .timeout(const Duration(seconds: 4));
        if (res.statusCode >= 200 && res.statusCode < 500) {
          baseUrl = base;
          return res;
        }
      } catch (_) {}
    }
    throw Exception('Failed to connect to Kalisi API');
  }

  // Helper method for resilient HTTP PUT
  Future<http.Response> _put(String endpoint, Map<String, dynamic> body) async {
    for (final base in candidateUrls) {
      try {
        final res = await http
            .put(
              Uri.parse('$base$endpoint'),
              headers: _headers,
              body: jsonEncode(body),
            )
            .timeout(const Duration(seconds: 4));
        if (res.statusCode >= 200 && res.statusCode < 500) {
          baseUrl = base;
          return res;
        }
      } catch (_) {}
    }
    throw Exception('Failed to connect to Kalisi API');
  }

  // 1. Auth API (/api/auth/register, /api/auth/login)
  Future<Map<String, dynamic>> loginOrRegister({
    String? fullName,
    String? email,
    String? password,
  }) async {
    final finalEmail = email ?? 'demo_guest_${DateTime.now().millisecondsSinceEpoch % 10000}@kalisi.app';
    final finalName = fullName ?? 'Demo Member';
    final finalPass = password ?? 'kalisi1234';

    try {
      final res = await _post('/auth/register', {
        'full_name': finalName,
        'email': finalEmail,
        'password': finalPass,
        'city': currentCity,
      });

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        token = data['access_token'];
        currentUserId = data['user_id'];
        currentUserName = data['full_name'];
        return data;
      }
    } catch (_) {}

    // Fallback: Login if already registered
    final loginRes = await _post('/auth/login', {'email': finalEmail, 'password': finalPass});
    if (loginRes.statusCode == 200) {
      final data = jsonDecode(loginRes.body);
      token = data['access_token'];
      currentUserId = data['user_id'];
      currentUserName = data['full_name'];
      return data;
    }

    throw Exception('Failed to authenticate');
  }

  // 2. Vibe DNA Quiz APIs (/api/vibe-dna/quiz, /api/vibe-dna/submit)
  Future<List<QuizQuestion>> getQuizQuestions() async {
    try {
      final res = await _get('/vibe-dna/quiz');
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((q) => QuizQuestion.fromJson(q)).toList();
      }
    } catch (_) {}

    // Safe offline fallback
    return [
      QuizQuestion(
        id: 'q1',
        question: 'How do you usually break the ice in a room full of strangers?',
        highlight: 'break the ice',
        options: ['Humor', 'Observation', 'Listening', 'Asking questions'],
      ),
      QuizQuestion(
        id: 'q2',
        question: 'What kind of conversations energize you most?',
        highlight: 'energize you most',
        options: ['Deep life stories & philosophy', 'Witty banter & pop culture', 'Passionate debates on ideas', 'Funny embarrassing moments'],
      ),
      QuizQuestion(
        id: 'q3',
        question: 'At a 5-person dinner table, your natural energy is...',
        highlight: 'natural energy',
        options: ['The Spark (high energy & laughs)', 'The Anchor (warm & attentive)', 'The Storyteller (quirky tales)', 'The Inquirer (thoughtful questions)'],
      ),
    ];
  }

  Future<VibeDNAResult> submitQuiz(Map<String, String> answers) async {
    try {
      final res = await _post('/vibe-dna/submit', {'answers': answers});
      if (res.statusCode == 200) {
        return VibeDNAResult.fromJson(jsonDecode(res.body));
      }
    } catch (_) {}

    return VibeDNAResult(
      archetype: 'Stark',
      title: 'The Charismatic Spark',
      description: 'Quick-witted, infectious energy, effortlessly brings laughter to the table.',
      superpower: 'Turns awkward silences into inside jokes within 60 seconds.',
      icebreakerStyle: 'Humor & Banter',
    );
  }

  // 3. Customization & Preferences API (/api/preferences/update)
  Future<void> updatePreferences({
    required String budgetTier,
    String dietary = 'No dietary restrictions',
    String language = 'English',
  }) async {
    try {
      await _put('/preferences/update', {
        'budget_tier': budgetTier,
        'dietary_requirements': dietary,
        'preferred_language': language,
      });
    } catch (_) {}
  }

  // 4. City Slots Discovery & Booking APIs (/api/slots/?city=, /api/slots/book)
  Future<List<CitySlot>> getCitySlots({String? city}) async {
    final targetCity = Uri.encodeComponent(city ?? currentCity);
    try {
      final res = await _get('/slots/?city=$targetCity');
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((s) => CitySlot.fromJson(s)).toList();
      }
    } catch (_) {}
    return [];
  }

  Future<String> bookSlot(String slotId) async {
    final res = await _post('/slots/book', {'slot_id': slotId});
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      return data['booking_id'];
    }
    throw Exception('Failed to book slot');
  }

  // 5. Progressive Reveal API (/api/reveal/{booking_id})
  Future<TableReveal> getTableReveal(String bookingId) async {
    final res = await _get('/reveal/$bookingId');
    if (res.statusCode == 200) {
      return TableReveal.fromJson(jsonDecode(res.body));
    }
    throw Exception('Failed to load reveal state');
  }
}
