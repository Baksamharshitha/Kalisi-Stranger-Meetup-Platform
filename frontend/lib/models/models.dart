class QuizQuestion {
  final String id;
  final String question;
  final String subtitle;
  final String highlight;
  final String type;
  final List<String> options;
  final String category;

  QuizQuestion({
    required this.id,
    required this.question,
    this.subtitle = '',
    this.highlight = '',
    this.type = 'single_choice',
    required this.options,
    this.category = 'vibe',
  });

  factory QuizQuestion.fromJson(Map<String, dynamic> json) {
    return QuizQuestion(
      id: json['id'] ?? '',
      question: json['question'] ?? '',
      subtitle: json['subtitle'] ?? '',
      highlight: json['highlight'] ?? '',
      type: json['type'] ?? 'single_choice',
      options: List<String>.from(json['options'] ?? []),
      category: json['category'] ?? 'vibe',
    );
  }
}

class VibeDNAResult {
  final String archetype;
  final String title;
  final String description;
  final String superpower;
  final String icebreakerStyle;

  VibeDNAResult({
    required this.archetype,
    required this.title,
    required this.description,
    required this.superpower,
    required this.icebreakerStyle,
  });

  factory VibeDNAResult.fromJson(Map<String, dynamic> json) {
    return VibeDNAResult(
      archetype: json['archetype'] ?? 'Clark Kent',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      superpower: json['superpower'] ?? '',
      icebreakerStyle: json['icebreaker_style'] ?? '',
    );
  }
}

class CitySlot {
  final String id;
  final String title;
  final String city;
  final String dateStr;
  final String timeWindow;
  final String status;
  final int priceInr;
  final int maxCapacity;
  final int seatsLeft;
  final bool isBookedByUser;
  final bool isEnabled;
  final String venueName;
  final String venueAddress;
  final String aboutEvent;
  final String rulesAndRegulations;

  CitySlot({
    required this.id,
    this.title = 'Weekend Stranger Dinner Meetup',
    required this.city,
    required this.dateStr,
    required this.timeWindow,
    required this.status,
    this.priceInr = 499,
    this.maxCapacity = 10,
    this.seatsLeft = 5,
    required this.isBookedByUser,
    this.isEnabled = true,
    this.venueName = 'Curated Partner Restaurant',
    this.venueAddress = 'Central City Location',
    this.aboutEvent = 'Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.',
    this.rulesAndRegulations = '1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food & drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only.',
  });

  factory CitySlot.fromJson(Map<String, dynamic> json) {
    return CitySlot(
      id: json['id'] ?? '',
      title: json['title'] ?? 'Weekend Stranger Dinner Meetup',
      city: json['city'] ?? '',
      dateStr: json['date_str'] ?? '',
      timeWindow: json['time_window'] ?? '',
      status: json['status'] ?? 'open',
      priceInr: json['price_inr'] ?? 499,
      maxCapacity: json['max_capacity'] ?? 10,
      seatsLeft: json['seats_left'] ?? 5,
      isBookedByUser: json['is_booked_by_user'] ?? false,
      isEnabled: json['is_enabled'] ?? (json['status'] == 'open'),
      venueName: json['venue_name'] ?? 'Curated Partner Restaurant',
      venueAddress: json['venue_address'] ?? 'Central City Location',
      aboutEvent: json['about_event'] ?? 'Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.',
      rulesAndRegulations: json['rules_and_regulations'] ?? '1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food & drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only.',
    );
  }
}

class CharacterInsight {
  final String archetype;
  final int count;
  final String vibeDescription;
  final String conversationStarter;

  CharacterInsight({
    required this.archetype,
    required this.count,
    required this.vibeDescription,
    required this.conversationStarter,
  });

  factory CharacterInsight.fromJson(Map<String, dynamic> json) {
    return CharacterInsight(
      archetype: json['archetype'] ?? '',
      count: json['count'] ?? 0,
      vibeDescription: json['vibe_description'] ?? '',
      conversationStarter: json['conversation_starter'] ?? '',
    );
  }
}

class TableReveal {
  final String bookingId;
  final String revealStage; // locked, area_revealed, fully_revealed
  final String dateStr;
  final String timeWindow;
  final String city;
  final String? neighborhood;
  final int? tableNumber;
  final String? restaurantName;
  final String? restaurantAddress;
  final String? cuisine;
  final String? groupSummary;
  final List<CharacterInsight> characterInsights;

  TableReveal({
    required this.bookingId,
    required this.revealStage,
    required this.dateStr,
    required this.timeWindow,
    required this.city,
    this.neighborhood,
    this.tableNumber,
    this.restaurantName,
    this.restaurantAddress,
    this.cuisine,
    this.groupSummary,
    required this.characterInsights,
  });

  factory TableReveal.fromJson(Map<String, dynamic> json) {
    return TableReveal(
      bookingId: json['booking_id'] ?? '',
      revealStage: json['reveal_stage'] ?? 'locked',
      dateStr: json['date_str'] ?? '',
      timeWindow: json['time_window'] ?? '',
      city: json['city'] ?? '',
      neighborhood: json['neighborhood'],
      tableNumber: json['table_number'],
      restaurantName: json['restaurant_name'],
      restaurantAddress: json['restaurant_address'],
      cuisine: json['cuisine'],
      groupSummary: json['group_summary'],
      characterInsights: (json['character_insights'] as List? ?? [])
          .map((i) => CharacterInsight.fromJson(i))
          .toList(),
    );
  }
}
