import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

class ApiService {
  // Singleton pattern
  static final ApiService instance = ApiService._internal();
  ApiService._internal();

  // Primary: 127.0.0.1 (via adb reverse tcp:8000 tcp:8000) / 10.98.89.130 (Host Wi-Fi LAN IP)
  static final List<String> candidateUrls = [
    'http://127.0.0.1:8000/api',
    'http://10.98.89.130:8000/api',
    'http://10.0.2.2:8000/api',
    'http://10.255.129.130:8000/api',
    'http://localhost:8000/api',
  ];
  static String baseUrl = 'http://127.0.0.1:8000/api';
  
  String? token;
  String? currentUserId;
  String? currentUserName;
  String currentCity = 'Hyderabad';

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
            .timeout(const Duration(seconds: 2));
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
            .timeout(const Duration(seconds: 2));
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
            .timeout(const Duration(seconds: 2));
        if (res.statusCode >= 200 && res.statusCode < 500) {
          baseUrl = base;
          return res;
        }
      } catch (_) {}
    }
    throw Exception('Failed to connect to Kalisi API');
  }

  // Helper method for resilient HTTP DELETE
  Future<http.Response> _delete(String endpoint) async {
    for (final base in candidateUrls) {
      try {
        final res = await http
            .delete(Uri.parse('$base$endpoint'), headers: _headers)
            .timeout(const Duration(seconds: 2));
        if (res.statusCode >= 200 && res.statusCode < 500) {
          baseUrl = base;
          return res;
        }
      } catch (_) {}
    }
    throw Exception('Failed to connect to Kalisi API');
  }

  // Ensure Authenticated Helper
  Future<void> ensureAuthenticated() async {
    if (token != null && currentUserId != null) return;
    try {
      await loginOrRegister(
        email: 'sathwik.kalisi@gmail.com',
        fullName: 'Sathwik',
        password: 'kalisi1234',
      );
    } catch (_) {
      try {
        await loginOrRegister(
          email: 'user_bangalore@kalisi.app',
          fullName: 'Rahul Verma',
          password: 'kalisi1234',
        );
      } catch (_) {}
    }
    // Auto-sync stored FCM push token once authenticated
    try {
      final prefs = await SharedPreferences.getInstance();
      final fcm = prefs.getString('fcm_token');
      if (fcm != null && fcm.isNotEmpty) {
        await registerFcmToken(fcm);
      }
    } catch (_) {}
  }

  // 1. Auth API
  Future<Map<String, dynamic>> loginOrRegister({
    String? fullName,
    String? email,
    String? password,
  }) async {
    final finalEmail = email ?? 'demo_guest_${DateTime.now().millisecondsSinceEpoch % 10000}@kalisi.app';
    final finalName = fullName ?? 'Kalisi Member';
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

  // OTP Verification APIs
  Future<Map<String, dynamic>> sendOtp(String phone) async {
    final res = await _post('/auth/send-otp', {'phone': phone});
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    throw Exception(jsonDecode(res.body)['detail'] ?? 'Failed to send OTP');
  }

  Future<Map<String, dynamic>> verifyOtp(String phone, String otp) async {
    final res = await _post('/auth/verify-otp', {'phone': phone, 'otp': otp});
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    throw Exception(jsonDecode(res.body)['detail'] ?? 'Invalid OTP code');
  }

  // Complete Onboarding (20 questions submission + OTP)
  Future<Map<String, dynamic>> completeOnboarding({
    required String fullName,
    required int age,
    required String gender,
    required String city,
    required String phone,
    required String otp,
    required Map<String, dynamic> answers,
  }) async {
    final res = await _post('/auth/onboarding-complete', {
      'full_name': fullName,
      'age': age,
      'gender': gender,
      'city': city,
      'phone': phone,
      'otp': otp,
      'answers': answers,
    });

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      token = data['access_token'];
      currentUserId = data['user_id'];
      currentUserName = data['full_name'];
      currentCity = data['city'] ?? city;
      return data;
    }
    throw Exception(jsonDecode(res.body)['detail'] ?? 'Failed to complete onboarding');
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

    // 20-step curated fallback
    return [
      QuizQuestion(id: 'full_name', question: "What's your full name?", subtitle: 'How should your tablemates address you?', type: 'text', options: [], category: 'identity'),
      QuizQuestion(id: 'age', question: 'How old are you?', subtitle: 'Helps us match age-compatible dinner groups.', type: 'age', options: ['18-22', '23-27', '28-34', '35-42', '43+'], category: 'identity'),
      QuizQuestion(id: 'gender', question: "What's your gender?", subtitle: 'Ensures balanced, comfortable dinner tables.', type: 'single_choice', options: ['Male', 'Female', 'Non-binary', 'Prefer not to say'], category: 'identity'),
      QuizQuestion(id: 'city', question: 'Which city are you currently in?', subtitle: 'Where would you like to attend dinner meetups?', type: 'single_choice', options: ['Hyderabad', 'Bangalore', 'Chennai', 'Mumbai'], category: 'identity'),
      QuizQuestion(id: 'intent', question: 'What brings you to Kalisi?', subtitle: 'Your main intention for joining a stranger dinner table.', type: 'single_choice', options: ['Make genuine new friends', 'Share great conversations & food', 'Step out of my comfort zone', 'Try new dining experiences'], category: 'vibe'),
      QuizQuestion(id: 'friend_description', question: 'How would your closest friends describe you?', subtitle: 'Your natural persona around friends.', type: 'single_choice', options: ['The witty spark who brings laughs', 'The calm anchor who keeps things grounded', 'The adventurous soul ready for anything', 'The thoughtful listener with deep insights'], category: 'vibe'),
      QuizQuestion(id: 'approach_strangers', question: 'How do you approach a room full of strangers?', subtitle: 'Your signature icebreaker style.', type: 'single_choice', options: ['Say hello with an open smile', 'Crack a lighthearted witty joke', 'Observe the room first, then jump in', 'Wait for someone to start the conversation'], category: 'vibe'),
      QuizQuestion(id: 'conversation_style', question: "What's your preferred conversation style?", subtitle: 'Dialogues that keep you hooked all evening.', type: 'single_choice', options: ['Witty banter & rapid pop-culture humor', 'Deep life stories, philosophies & dreams', 'Curious questions & uncovering passions', 'Random rabbit holes & quirky observations'], category: 'social'),
      QuizQuestion(id: 'group_role', question: 'At a 5-person dinner table, your natural energy is…', subtitle: 'The role you effortlessly step into.', type: 'single_choice', options: ['The Spark (keeps energy high & laughter alive)', 'The Anchor (makes everyone feel heard & safe)', 'The Storyteller (brings unexpected real-life stories)', 'The Inquirer (asks thoughtful questions)'], category: 'social'),
      QuizQuestion(id: 'awkward_silences', question: 'How do you handle an awkward pause at the table?', subtitle: 'When the conversation momentarily drops...', type: 'single_choice', options: ['Drop a humorous self-deprecating comment', 'Ask a wild, intriguing hypothetical question', 'Comfortably sip my drink and let it be', 'Smoothly introduce a fresh, exciting topic'], category: 'social'),
      QuizQuestion(id: 'recharge_style', question: 'How does your social battery recharge best?', subtitle: 'After an eventful weekend...', type: 'single_choice', options: ['Solo quiet time with books or a movie', 'Putting on headphones and vibing to music', 'Low-key hangout with 1 or 2 close friends', 'Deep uninterrupted 9-hour sleep'], category: 'social'),
      QuizQuestion(id: 'spontaneity', question: 'How spontaneous are you when plans change?', subtitle: 'Your comfort with surprise twists and turns.', type: 'single_choice', options: ['A structured planner (Prefer clear agendas)', 'Balanced & flexible (I easily go with the flow)', 'Wildly spontaneous (Say yes first, figure it out later!)'], category: 'vibe'),
      QuizQuestion(id: 'favorite_topic', question: 'What topic energizes you most at a dinner table?', subtitle: 'What makes you lose track of time?', type: 'single_choice', options: ['Travel tales, bucket lists & road trips', 'Cinema, music, books & pop culture', 'Big ideas, startup stories & ambitions', 'Food culture, secret recipes & hidden gems'], category: 'entertainment'),
      QuizQuestion(id: 'time_machine_era', question: 'If you had a time machine for one dinner, which era would you revisit?', subtitle: 'A fun glimpse into your nostalgic aesthetic.', type: 'single_choice', options: ['The Retro 80s (Synthwave & disco grooves)', 'The Golden 90s (Cartoons, pop icons & mixtapes)', 'The Indie 2000s (Early internet & indie cafe culture)', 'The Futuristic 2050 (Cyberpunk & flying cars)'], category: 'entertainment'),
      QuizQuestion(id: 'table_activity', question: 'Which table activity would you pick?', subtitle: 'Entertainment to spark connection.', type: 'single_choice', options: ['Table card deck with spicy dilemmas', 'Hilarious party games & rapid trivia', 'Anthakshari & guessing nostalgic songs', 'Chef mystery food tasting & rating'], category: 'entertainment'),
      QuizQuestion(id: 'ideal_setting', question: 'Pick your ideal dinner meetup setting.', subtitle: 'The ambiance that gives you the best vibes.', type: 'single_choice', options: ['Breezy rooftop with panoramic city skyline', 'Warm, candlelit boutique café with cozy booths', 'Buzzing modern bistro with craft kitchen vibes', 'Hidden speakeasy with moody ambient jazz'], category: 'taste'),
      QuizQuestion(id: 'favorite_cuisine', question: "What's your go-to comfort cuisine?", subtitle: 'What makes your tastebuds happiest?', type: 'single_choice', options: ['Authentic Indian & Biryanis', 'Italian pastas & artisan woodfired pizzas', 'Pan-Asian ramen, sushi & dim sum', 'Mexican tacos, nachos & continental'], category: 'taste'),
      QuizQuestion(id: 'dietary_preference', question: 'What is your dietary preference?', subtitle: 'Essential for reserving the right restaurant menu.', type: 'single_choice', options: ['Vegetarian', 'Non-Vegetarian', 'Eggetarian', 'Vegan', 'Jain'], category: 'taste'),
      QuizQuestion(id: 'dinner_budget', question: "What's your comfortable dinner budget?", subtitle: 'Per-person food budget range.', type: 'single_choice', options: ['Under ₹500 (Budget-friendly)', '₹500 – ₹1,000 (Mid-Range comfort)', '₹1,000 – ₹2,000 (Premium dining & drinks)', '₹2,000+ (Exclusive fine dining luxury)'], category: 'taste'),
      QuizQuestion(id: 'phone_otp', question: "What's your mobile number?", subtitle: "We'll send an instant 6-digit OTP to verify your account & lock your seat.", type: 'phone_otp', options: [], category: 'verification'),
    ];
  }

  Future<VibeDNAResult> submitQuiz(Map<String, dynamic> answers) async {
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

  // 4. City Slots Discovery & Booking APIs (/api/slots/?city=, /api/slots/book, /api/slots/locations)
  Future<List<String>> getLocations() async {
    try {
      final res = await _get('/slots/locations');
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        if (list.isNotEmpty) {
          return list.map((e) => e.toString()).toList();
        }
      }
    } catch (_) {}
    return [
      'Central Bangalore',
      'Indiranagar Bangalore',
      'Koramangala Bangalore',
      'Anna Nagar Chennai',
      'South Mumbai',
    ];
  }

  Future<List<CitySlot>> getCitySlots({String? city}) async {
    final searchCity = city ?? currentCity;
    final targetCity = Uri.encodeComponent(searchCity);
    try {
      final res = await _get('/slots/?city=$targetCity');
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        // Return exact list returned by backend for this specific location
        return list.map((s) => CitySlot.fromJson(s)).toList();
      }
    } catch (_) {}

    // Resilient fallback slots matching the database when offline
    return getFallbackSlots(searchCity);
  }

  List<CitySlot> getFallbackSlots(String city) {
    final clean = city.toLowerCase();
    if (clean.contains('indiranagar')) {
      return [
        CitySlot(
          id: 'fa2c59d9-275a-495c-ba4f-a459d8418c6f',
          title: 'Saturday Pan-Asian Craft Dinner',
          city: 'Indiranagar Bangalore',
          dateStr: 'Sat, 11/28/2026',
          timeWindow: '20:00 - 22:45',
          status: 'open',
          priceInr: 649,
          maxCapacity: 10,
          seatsLeft: 5,
          isBookedByUser: false,
          isEnabled: true,
          venueName: 'The Fatty Bao 12th Main',
          venueAddress: '610, 12th Main Rd, HAL 2nd Stage, Indiranagar, Bengaluru',
          aboutEvent: 'A mouthwatering evening of steamed baos, artisan ramen, and delightful stranger icebreakers in a vibrant rooftop setting.',
          rulesAndRegulations: '1. Arrive on time to sit with your matched table.\n2. Equal bill split for appetizers and drinks.\n3. Be respectful and celebrate diverse perspectives.\n4. Age 18+ verified members.',
        ),
      ];
    } else if (clean.contains('koramangala')) {
      return [
        CitySlot(
          id: '2ff0deee-b198-4e86-9ddb-1a8d40e3d68c',
          title: 'Saturday Cozy Bistro Meetup',
          city: 'Koramangala Bangalore',
          dateStr: 'Sat, 11/28/2026',
          timeWindow: '19:00 - 21:30',
          status: 'open',
          priceInr: 499,
          maxCapacity: 10,
          seatsLeft: 6,
          isBookedByUser: false,
          isEnabled: true,
          venueName: 'Third Wave Coffee & Bistro',
          venueAddress: '80 Feet Rd, 4th Block, Koramangala, Bengaluru',
          aboutEvent: 'Cozy artisanal brews, wood-fired snacks, and deep conversations with 5 engaging new tablemates.',
          rulesAndRegulations: '1. Arrive within 15 minutes of scheduled start.\n2. Phone-free dining experience.\n3. Split table bills evenly.\n4. Age 18+ verified members.',
        ),
      ];
    } else if (clean.contains('chennai')) {
      return [
        CitySlot(
          id: 'fc41bc35-b3ad-4a92-9157-6e88501ecdd3',
          title: 'Saturday Mystery Potion Dinner',
          city: 'Anna Nagar Chennai',
          dateStr: 'Sat, 11/28/2026',
          timeWindow: '19:30 - 22:30',
          status: 'open',
          priceInr: 599,
          maxCapacity: 10,
          seatsLeft: 7,
          isBookedByUser: false,
          isEnabled: true,
          venueName: "Writer's Cafe Anna Nagar",
          venueAddress: '3rd Avenue, Anna Nagar East, Chennai',
          aboutEvent: 'Bookish charm, cozy artisanal desserts, and warm icebreakers connecting Chennai food lovers.',
          rulesAndRegulations: '1. Punctuality is appreciated.\n2. Equal bill splitting.\n3. Friendly, respectful dialogue.\n4. Age 18+ verified diners.',
        ),
      ];
    } else if (clean.contains('mumbai')) {
      return [
        CitySlot(
          id: '353fdf0a-4a7f-4440-9bf9-c1307c3d6f6d',
          title: 'Saturday Heritage Cafe Meetup',
          city: 'South Mumbai',
          dateStr: 'Sat, 11/28/2026',
          timeWindow: '19:30 - 22:30',
          status: 'open',
          priceInr: 799,
          maxCapacity: 10,
          seatsLeft: 5,
          isBookedByUser: false,
          isEnabled: true,
          venueName: 'Kala Ghoda Cafe Fort',
          venueAddress: '10 Ropewalk Lane, Kala Ghoda, Fort, Mumbai',
          aboutEvent: 'Artistic vibes, heritage architecture, and lively conversations in historic South Mumbai.',
          rulesAndRegulations: '1. Respect table boundaries.\n2. Equal bill splitting.\n3. Age 18+ verified attendees.',
        ),
      ];
    }

    // Default Central Bangalore Slots
    return [
      CitySlot(
        id: '75268e8b-ca03-43cf-b6a7-d98e89101927',
        title: 'Saturday Sunset Stranger Dinner',
        city: 'Central Bangalore',
        dateStr: 'Sat, 11/28/2026',
        timeWindow: '19:30 - 22:30',
        status: 'open',
        priceInr: 599,
        maxCapacity: 10,
        seatsLeft: 4,
        isBookedByUser: false,
        isEnabled: true,
        venueName: 'Smoke House Deli Lavelle Road',
        venueAddress: '52, Ground Floor, Lavelle Road, Shanthala Nagar, Ashok Nagar, Bengaluru',
        aboutEvent: 'Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.',
        rulesAndRegulations: '1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food & drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only.',
      ),
      CitySlot(
        id: 'e129dc31-cd68-4014-afb2-fdca82ea6fb7',
        title: 'Sunday Rooftop Skyline Dinner',
        city: 'Central Bangalore',
        dateStr: 'Sun, 11/29/2026',
        timeWindow: '20:00 - 23:00',
        status: 'open',
        priceInr: 699,
        maxCapacity: 10,
        seatsLeft: 6,
        isBookedByUser: false,
        isEnabled: true,
        venueName: 'Skyye Lounge UB City',
        venueAddress: 'UB City 16th Floor, Vittal Mallya Road, Bengaluru',
        aboutEvent: 'Enjoy breathtaking skyline views while getting to know fellow foodies over craft cocktails and signature tapas.',
        rulesAndRegulations: '1. Smart casual dress code.\n2. Equal bill splitting for food & drinks.\n3. Respect everyone at the table.\n4. Age 18+ verified diners only.',
      ),
    ];
  }

  Future<String> bookSlot(String slotId) async {
    try {
      final res = await _post('/slots/book', {'slot_id': slotId});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return data['booking_id'];
      }
    } catch (_) {}
    return 'demo-booking-${DateTime.now().millisecondsSinceEpoch}';
  }

  // 5. Progressive Reveal API (/api/reveal/{booking_id})
  Future<TableReveal> getTableReveal(String bookingId) async {
    final res = await _get('/reveal/$bookingId');
    if (res.statusCode == 200) {
      return TableReveal.fromJson(jsonDecode(res.body));
    }
    throw Exception('Failed to load reveal state');
  }

  // 6. User Profile Bookings (Booked & Attended)
  Future<Map<String, List<dynamic>>> getUserBookings() async {
    await ensureAuthenticated();
    try {
      final res = await _get('/auth/user-bookings');
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return {
          'booked': List<dynamic>.from(data['booked'] ?? []),
          'attended': List<dynamic>.from(data['attended'] ?? []),
        };
      }
    } catch (_) {}
    return {'booked': [], 'attended': []};
  }

  // 7. Password Change
  Future<void> changePassword(String currentPassword, String newPassword) async {
    await ensureAuthenticated();
    final res = await _put('/auth/change-password', {
      'current_password': currentPassword,
      'new_password': newPassword,
    });
    if (res.statusCode != 200) {
      final body = jsonDecode(res.body);
      throw Exception(body['detail'] ?? 'Failed to update password');
    }
  }

  // 8. Delete Account
  Future<void> deleteAccount() async {
    await ensureAuthenticated();
    final res = await _delete('/auth/delete-account');
    if (res.statusCode == 200) {
      token = null;
      currentUserId = null;
      currentUserName = null;
      return;
    }
    throw Exception('Failed to delete account');
  }

  // 9. User & Community Videos
  Future<Map<String, List<dynamic>>> getUserVideos() async {
    await ensureAuthenticated();
    try {
      final res = await _get('/auth/user-videos');
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return {
          'uploaded': List<dynamic>.from(data['uploaded'] ?? []),
          'community': List<dynamic>.from(data['community'] ?? []),
        };
      }
    } catch (_) {}
    return {'uploaded': [], 'community': []};
  }

  // 10. Upload Video Reel
  Future<void> uploadVideo({
    required String title,
    required String venueName,
    required String videoUrl,
    String? thumbnailUrl,
  }) async {
    await ensureAuthenticated();
    final res = await _post('/auth/upload-video', {
      'title': title,
      'venue_name': venueName,
      'video_url': videoUrl,
      'thumbnail_url': thumbnailUrl ?? 'https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80',
    });
    if (res.statusCode != 200) {
      final body = jsonDecode(res.body);
      throw Exception(body['detail'] ?? 'Failed to upload video');
    }
  }

  // 11. Register Firebase FCM Push Token
  Future<void> registerFcmToken(String fcmToken) async {
    try {
      await _post('/auth/register-fcm-token', {'fcm_token': fcmToken});
    } catch (_) {}
  }

  // 12. Helper to resolve relative media URLs (e.g. /uploads/videos/...)
  String resolveMediaUrl(String? urlOrPath) {
    if (urlOrPath == null || urlOrPath.isEmpty) {
      return 'https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80';
    }
    if (urlOrPath.startsWith('http://') || urlOrPath.startsWith('https://')) {
      return urlOrPath;
    }
    final host = baseUrl.replaceAll('/api', '');
    return '$host${urlOrPath.startsWith('/') ? '' : '/'}$urlOrPath';
  }
}
