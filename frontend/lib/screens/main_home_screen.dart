import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../services/notification_service.dart';
import 'onboarding_quiz_screen.dart';
import 'welcome_screen.dart';
import 'event_details_screen.dart';
import 'my_bookings_screen.dart';

class MainHomeScreen extends StatefulWidget {
  final int initialTabIndex;

  const MainHomeScreen({super.key, this.initialTabIndex = 0});

  @override
  State<MainHomeScreen> createState() => _MainHomeScreenState();
}

class _MainHomeScreenState extends State<MainHomeScreen> {
  int _currentTabIndex = 0;
  String _selectedLocation = 'Central Bangalore';
  List<CitySlot> _slots = [];
  bool _isLoading = true;

  // Profile Section State
  List<dynamic> _bookedList = [];
  List<dynamic> _attendedList = [];
  List<dynamic> _uploadedVideos = [];
  List<dynamic> _communityVideos = [];
  bool _notificationsAllowed = false;

  final List<String> _availableLocations = [
    'Central Bangalore',
    'Indiranagar Bangalore',
    'Koramangala Bangalore',
    'Anna Nagar Chennai',
    'South Mumbai',
  ];

  @override
  void initState() {
    super.initState();
    _currentTabIndex = widget.initialTabIndex;
    _initUserAndSlots();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkMandatoryNotifications();
    });
  }

  Future<void> _initUserAndSlots() async {
    await ApiService.instance.ensureAuthenticated();
    if (mounted) {
      setState(() {});
    }
    await Future.wait([
      _fetchSlots(),
      _loadProfileData(),
      _loadLocations(),
    ]);
  }

  Future<void> _loadLocations() async {
    try {
      final locs = await ApiService.instance.getLocations();
      if (mounted && locs.isNotEmpty) {
        setState(() {
          _availableLocations.clear();
          _availableLocations.addAll(locs);
        });
      }
    } catch (_) {}
  }

  Future<void> _loadProfileData() async {
    try {
      final bookingsData = await ApiService.instance.getUserBookings();
      final videosData = await ApiService.instance.getUserVideos();
      final notifStatus = await NotificationService.isPermissionGranted();
      if (mounted) {
        setState(() {
          _bookedList = bookingsData['booked'] ?? [];
          _attendedList = bookingsData['attended'] ?? [];
          _uploadedVideos = videosData['uploaded'] ?? [];
          _communityVideos = videosData['community'] ?? [];
          _notificationsAllowed = notifStatus;
        });
      }
    } catch (_) {}
  }

  Future<void> _checkMandatoryNotifications() async {
    // Wait for initial screen transition (e.g. from Splash) to finish before prompting
    await Future.delayed(const Duration(milliseconds: 1200));
    if (!mounted) return;
    final granted = await NotificationService.isPermissionGranted();
    if (mounted) {
      setState(() => _notificationsAllowed = granted);
    }
    if (!granted && mounted) {
      _showMandatoryNotificationModal();
    }
  }

  void _showMandatoryNotificationModal() {
    if (!mounted) return;
    showDialog(
      context: context,
      useRootNavigator: true,
      barrierDismissible: false,
      builder: (ctx) {
        return PopScope(
          canPop: false,
          child: StatefulBuilder(
            builder: (dialogCtx, setDialogState) {
              return AlertDialog(
                backgroundColor: const Color(0xFF141414),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(24),
                  side: const BorderSide(color: Color(0xFFF5A623), width: 1.2),
                ),
                contentPadding: const EdgeInsets.all(24),
                content: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 64,
                      height: 64,
                      decoration: BoxDecoration(
                        color: const Color(0xFFF5A623).withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                        border: Border.all(color: const Color(0xFFF5A623), width: 1.5),
                      ),
                      child: const Icon(
                        Icons.notifications_active,
                        color: Color(0xFFF5A623),
                        size: 32,
                      ),
                    ),
                    const SizedBox(height: 18),
                    const Text(
                      'Notifications are Mandatory',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.2,
                      ),
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Kalisi curates mystery dining with verified strangers. Push notifications are strictly mandatory to receive your secret restaurant address, table reveal, and attendance alerts.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 13,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E1E1E),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFF2E2E2E)),
                      ),
                      child: const Column(
                        children: [
                          _MandatoryFeatureRow(icon: Icons.lock_open, text: 'Secret Restaurant Reveal (Sat 10:00 AM)'),
                          SizedBox(height: 8),
                          _MandatoryFeatureRow(icon: Icons.groups, text: 'Table Group & Stranger Matches'),
                          SizedBox(height: 8),
                          _MandatoryFeatureRow(icon: Icons.alarm, text: 'T-2 Hours Attendance Confirmation'),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.check_circle, size: 18),
                        onPressed: () async {
                          final granted = await NotificationService.requestPermission();
                          if (granted) {
                            if (mounted) {
                              setState(() => _notificationsAllowed = true);
                            }
                            if (ctx.mounted) Navigator.pop(ctx);
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('✅ Notifications enabled! You will receive table reveals.'),
                                  backgroundColor: Color(0xFF4CAF50),
                                ),
                              );
                            }
                          } else {
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('⚠️ Push notifications are mandatory to attend Kalisi dinners.'),
                                  backgroundColor: Color(0xFFD32F2F),
                                ),
                              );
                            }
                          }
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFF5A623),
                          foregroundColor: Colors.black,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(24),
                          ),
                          elevation: 0,
                        ),
                        label: const Text(
                          'Enable Push Notifications',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  Future<void> _fetchSlots() async {
    setState(() => _isLoading = true);
    try {
      final slots = await ApiService.instance.getCitySlots(city: _selectedLocation);
      if (mounted) {
        setState(() {
          _slots = slots;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showLocationPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF161616),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                const Text(
                  'Select Your Neighborhood',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 12),
                ..._availableLocations.map((loc) {
                  final isSelected = loc == _selectedLocation;
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(
                      Icons.location_on,
                      color: isSelected ? const Color(0xFFF5A623) : Colors.white54,
                    ),
                    title: Text(
                      loc,
                      style: TextStyle(
                        color: isSelected ? const Color(0xFFF5A623) : Colors.white,
                        fontWeight: isSelected ? FontWeight.w800 : FontWeight.w500,
                      ),
                    ),
                    trailing: isSelected
                        ? const Icon(Icons.check, color: Color(0xFFF5A623))
                        : null,
                    onTap: () {
                      Navigator.pop(ctx);
                      setState(() {
                        _selectedLocation = loc;
                        ApiService.instance.currentCity = loc;
                      });
                      _fetchSlots();
                    },
                  );
                }),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showHowItWorksModal() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF161616),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                const Row(
                  children: [
                    Icon(Icons.auto_awesome, color: Color(0xFFBA68C8), size: 22),
                    SizedBox(width: 10),
                    Text(
                      'How Kalisi Works',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _buildStepRow('1', 'Vibe DNA Quiz', 'Answer 3 quick questions to discover your conversational persona.'),
                const SizedBox(height: 14),
                _buildStepRow('2', 'Book Your Seat', 'Pick your preferred weekend dinner slot in your city.'),
                const SizedBox(height: 14),
                _buildStepRow('3', 'Progressive Reveal', 'Your curated restaurant & table number unlock progressively on event morning.'),
                const SizedBox(height: 14),
                _buildStepRow('4', 'Dine with 5 Strangers', 'Show up, share a delicious meal, and leave with new friends!'),
                const SizedBox(height: 20),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildStepRow(String number, String title, String subtitle) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: const Color(0xFFBA68C8), width: 1.5),
          ),
          alignment: Alignment.center,
          child: Text(
            number,
            style: const TextStyle(
              color: Color(0xFFBA68C8),
              fontSize: 13,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: const TextStyle(
                  color: Colors.white60,
                  fontSize: 13,
                  height: 1.3,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: IndexedStack(
        index: _currentTabIndex,
        children: [
          _buildEventsView(),
          _buildReelsView(),
          _buildNotificationsView(),
          _buildProfileView(),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Colors.black,
          border: Border(top: BorderSide(color: Color(0xFF1F1F1F), width: 0.8)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentTabIndex,
          onTap: (index) => setState(() => _currentTabIndex = index),
          backgroundColor: Colors.black,
          type: BottomNavigationBarType.fixed,
          selectedItemColor: Colors.white,
          unselectedItemColor: const Color(0xFFBA68C8),
          selectedLabelStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800),
          unselectedLabelStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
          items: const [
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.only(bottom: 4),
                child: Icon(Icons.calendar_month, size: 24),
              ),
              label: 'Events',
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.only(bottom: 4),
                child: Icon(Icons.play_circle_outline, size: 24),
              ),
              label: 'Reels',
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.only(bottom: 4),
                child: Icon(Icons.notifications_none, size: 24),
              ),
              label: 'Notifications',
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.only(bottom: 4),
                child: Icon(Icons.person_outline, size: 24),
              ),
              label: 'Profile',
            ),
          ],
        ),
      ),
    );
  }

  // ===========================================================================
  // 1. EVENTS VIEW (Matches uploaded image pixel-by-pixel)
  // ===========================================================================
  Widget _buildEventsView() {
    final userName = ApiService.instance.currentUserName ?? 'user';

    return SafeArea(
      top: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top Hero Restaurant Background with Overlay
          Stack(
            children: [
              // Background Image with dark restaurant atmosphere
              Container(
                height: 250,
                width: double.infinity,
                decoration: const BoxDecoration(
                  image: DecorationImage(
                    image: NetworkImage(
                      'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
                    ),
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              // Gradient Overlay fading into pure black
              Container(
                height: 250,
                width: double.infinity,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.black54,
                      Color(0xCC000000),
                      Colors.black,
                    ],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
              ),
              // Content on top of background
              Padding(
                padding: const EdgeInsets.only(top: 50, left: 24, right: 24, bottom: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Hey user 👋
                    Text(
                      'Hey $userName 👋',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 26,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.3,
                      ),
                    ),
                    const SizedBox(height: 14),

                    // "Meet new people in" + Top right ? and ↻ buttons
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        const Text(
                          'Meet new people in',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 26,
                            fontWeight: FontWeight.w400,
                            letterSpacing: -0.2,
                          ),
                        ),
                        // Circular outline buttons: ? and ↻
                        Row(
                          children: [
                            // Help / How it works button
                            InkWell(
                              onTap: _showHowItWorksModal,
                              borderRadius: BorderRadius.circular(20),
                              child: Container(
                                width: 34,
                                height: 34,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: const Color(0xFFBA68C8),
                                    width: 1.2,
                                  ),
                                ),
                                alignment: Alignment.center,
                                child: const Icon(
                                  Icons.help_outline,
                                  color: Color(0xFFBA68C8),
                                  size: 18,
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            // Refresh button
                            InkWell(
                              onTap: _fetchSlots,
                              borderRadius: BorderRadius.circular(20),
                              child: Container(
                                width: 34,
                                height: 34,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: const Color(0xFFBA68C8),
                                    width: 1.2,
                                  ),
                                ),
                                alignment: Alignment.center,
                                child: const Icon(
                                  Icons.refresh,
                                  color: Color(0xFFBA68C8),
                                  size: 18,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Gold Border Location Pill (Compact & Length Decreased)
                    InkWell(
                      onTap: _showLocationPicker,
                      borderRadius: BorderRadius.circular(20),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0xFF141414),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: const Color(0xFFC89B3C),
                            width: 1.0,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.location_on,
                              color: Color(0xFFE2B755),
                              size: 14,
                            ),
                            const SizedBox(width: 5),
                            ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 160),
                              child: Text(
                                _selectedLocation,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: Color(0xFFE2B755),
                                  fontSize: 13,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            const SizedBox(width: 4),
                            const Icon(
                              Icons.keyboard_arrow_down,
                              color: Color(0xFFE2B755),
                              size: 16,
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),

                    // Subtext: "X events available - Book yours now!!"
                    Text(
                      '${_slots.length} events available - Book yours now!!',
                      style: const TextStyle(
                        color: Color(0xFF9E9E9E),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        letterSpacing: 0.1,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Events List or Empty State
          Expanded(
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      color: Color(0xFFF5A623),
                    ),
                  )
                : _slots.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24),
                          child: Text(
                            'Oops no slots available around you right now!',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 16,
                              fontWeight: FontWeight.w400,
                              letterSpacing: 0.1,
                            ),
                          ),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                        itemCount: _slots.length,
                        itemBuilder: (context, index) {
                          final slot = _slots[index];

                          return GestureDetector(
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => EventDetailsScreen(slot: slot),
                                ),
                              ).then((_) => _fetchSlots());
                            },
                            child: Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
                              decoration: BoxDecoration(
                                color: const Color(0xFF141414),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: slot.isBookedByUser
                                      ? const Color(0xFFF5A623).withValues(alpha: 0.6)
                                      : const Color(0xFF262626),
                                  width: slot.isBookedByUser ? 1.5 : 1.0,
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // Top Row: Category Chip & Price
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF222222),
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: Row(
                                          children: [
                                            const Icon(Icons.groups, color: Color(0xFFBA68C8), size: 12),
                                            const SizedBox(width: 5),
                                            ConstrainedBox(
                                              constraints: const BoxConstraints(maxWidth: 140),
                                              child: Text(
                                                slot.city,
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                  color: Color(0xFFBA68C8),
                                                  fontSize: 10,
                                                  fontWeight: FontWeight.w800,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Text(
                                        '₹${slot.priceInr}',
                                        style: const TextStyle(
                                          color: Color(0xFFF5A623),
                                          fontSize: 17,
                                          fontWeight: FontWeight.w900,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),

                                  // Event Name / Title
                                  Text(
                                    slot.title,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 15,
                                      fontWeight: FontWeight.w800,
                                      letterSpacing: -0.2,
                                    ),
                                  ),
                                  const SizedBox(height: 5),

                                  // Date & Time
                                  Row(
                                    children: [
                                      const Icon(Icons.calendar_today, color: Color(0xFFF5A623), size: 11),
                                      const SizedBox(width: 5),
                                      Text(
                                        slot.dateStr,
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 12,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      const Icon(Icons.access_time, color: Colors.white54, size: 11),
                                      const SizedBox(width: 4),
                                      Text(
                                        slot.timeWindow,
                                        style: const TextStyle(
                                          color: Colors.white70,
                                          fontSize: 12,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 5),

                                  // Spots Left & Venue Preview
                                  Row(
                                    children: [
                                      const Icon(Icons.event_seat_outlined, color: Colors.white38, size: 11),
                                      const SizedBox(width: 4),
                                      Text(
                                        '${slot.seatsLeft} spots left',
                                        style: const TextStyle(
                                          color: Colors.white60,
                                          fontSize: 11,
                                        ),
                                      ),
                                      const Spacer(),
                                      const Text(
                                        'Tap to view venue & rules',
                                        style: TextStyle(
                                          color: Color(0xFFBA68C8),
                                          fontSize: 10.5,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      const Icon(Icons.chevron_right, color: Color(0xFFBA68C8), size: 13),
                                    ],
                                  ),
                                  const SizedBox(height: 10),

                                  // Action Button
                                  SizedBox(
                                    width: double.infinity,
                                    height: 38,
                                    child: ElevatedButton.icon(
                                      icon: Icon(
                                        slot.isBookedByUser ? Icons.check_circle : Icons.arrow_forward,
                                        size: 15,
                                      ),
                                      onPressed: () {
                                        Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                            builder: (_) => EventDetailsScreen(slot: slot),
                                          ),
                                        ).then((_) => _fetchSlots());
                                      },
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: slot.isBookedByUser
                                            ? const Color(0xFF222222)
                                            : const Color(0xFFF5A623),
                                        foregroundColor: slot.isBookedByUser ? const Color(0xFFF5A623) : Colors.black,
                                        elevation: 0,
                                        padding: const EdgeInsets.symmetric(vertical: 0),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(14),
                                          side: slot.isBookedByUser
                                              ? const BorderSide(color: Color(0xFFF5A623))
                                              : BorderSide.none,
                                        ),
                                      ),
                                      label: Text(
                                        slot.isBookedByUser ? 'Seat Confirmed • View Details' : 'View Event & Book Seat',
                                        style: const TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w900,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  // ===========================================================================
  // 2. REELS VIEW
  // ===========================================================================
  Widget _buildReelsView() {
    final defaultReels = [
      {
        'title': 'First 5 Mins vs Last 5 Mins at Kalisi',
        'venue': 'Chamber of Potions, Anna Nagar',
        'views': '14.2K views',
        'image': 'https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80',
        'video_url': 'https://www.w3schools.com/html/mov_bbb.mp4',
      },
      {
        'title': 'What Happens When 5 Introverts Dine Together?',
        'venue': 'Central Bangalore Meetup',
        'views': '28.5K views',
        'image': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80',
        'video_url': 'https://www.w3schools.com/html/mov_bbb.mp4',
      },
      {
        'title': 'The Mystery Menu Taste Test with Strangers',
        'venue': 'The Fatty Bao, Indiranagar',
        'views': '9.8K views',
        'image': 'https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80',
        'video_url': 'https://www.w3schools.com/html/mov_bbb.mp4',
      },
    ];

    final reels = _communityVideos.isNotEmpty
        ? _communityVideos.map((v) => {
            'title': (v['title'] ?? 'Kalisi Table Moment').toString(),
            'venue': (v['venue_name'] ?? v['venue'] ?? 'Bangalore Stranger Dinner').toString(),
            'views': '${v['views_count'] ?? 1200} views',
            'image': ApiService.instance.resolveMediaUrl(v['thumbnail_url']?.toString()),
            'video_url': ApiService.instance.resolveMediaUrl(v['video_url']?.toString()),
          }).toList()
        : defaultReels;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Kalisi Reels',
                        style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'Real moments & unfiltered laughter from our dinner tables',
                        style: TextStyle(color: Colors.white60, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                InkWell(
                  onTap: _showUploadVideoDialog,
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF5A623).withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFFF5A623)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.video_call, color: Color(0xFFF5A623), size: 16),
                        SizedBox(width: 4),
                        Text(
                          'Upload',
                          style: TextStyle(color: Color(0xFFF5A623), fontSize: 12, fontWeight: FontWeight.w800),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: reels.length,
                itemBuilder: (context, index) {
                  final r = reels[index];
                  return Container(
                    margin: const EdgeInsets.only(bottom: 18),
                    height: 220,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(22),
                      image: DecorationImage(
                        image: NetworkImage(r['image']!),
                        fit: BoxFit.cover,
                      ),
                    ),
                    child: Stack(
                      children: [
                        Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(22),
                            gradient: const LinearGradient(
                              colors: [Colors.transparent, Colors.black87],
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                            ),
                          ),
                        ),
                        const Center(
                          child: Icon(Icons.play_circle_fill, color: Colors.white70, size: 54),
                        ),
                        Positioned(
                          bottom: 16,
                          left: 16,
                          right: 16,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                r['title']!,
                                style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w800),
                              ),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  const Icon(Icons.location_on, color: Color(0xFFF5A623), size: 12),
                                  const SizedBox(width: 4),
                                  Text(
                                    r['venue']!,
                                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                                  ),
                                  const Spacer(),
                                  Text(
                                    r['views']!,
                                    style: const TextStyle(color: Colors.white60, fontSize: 11),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ===========================================================================
  // 3. NOTIFICATIONS VIEW
  // ===========================================================================
  Widget _buildNotificationsView() {
    final notifications = [
      {
        'title': 'Table Matchmaking Confirmed!',
        'body': 'Your table for Saturday dinner in Central Bangalore is matched with 5 curious strangers.',
        'time': '10 mins ago',
        'icon': Icons.groups,
        'color': const Color(0xFFBA68C8),
      },
      {
        'title': 'Progressive Reveal Countdown',
        'body': 'Secret restaurant address will unlock on Saturday morning at 10:00 AM.',
        'time': '2 hours ago',
        'icon': Icons.lock_clock,
        'color': const Color(0xFFF5A623),
      },
      {
        'title': 'Welcome to Kalisi',
        'body': 'Your profile has been verified. Discover dinners near you anytime.',
        'time': '1 day ago',
        'icon': Icons.verified,
        'color': Colors.greenAccent,
      },
    ];

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Notifications',
              style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: notifications.length,
                itemBuilder: (context, index) {
                  final n = notifications[index];
                  return Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF141414),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: const Color(0xFF222222)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: (n['color'] as Color).withValues(alpha: 0.15),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(n['icon'] as IconData, color: n['color'] as Color, size: 20),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                n['title'] as String,
                                style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w800),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                n['body'] as String,
                                style: const TextStyle(color: Colors.white60, fontSize: 13, height: 1.3),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                n['time'] as String,
                                style: const TextStyle(color: Colors.white38, fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ===========================================================================
  // 4. PROFILE VIEW (Professional Revamp & Styled Menu Rows)
  // ===========================================================================
  Widget _buildProfileView() {
    final userName = ApiService.instance.currentUserName ?? 'Rahul Verma';

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _loadProfileData,
        color: const Color(0xFFF5A623),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Profile & Account',
                style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 16),

              // 1. Professional User Info Header Card
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: const Color(0xFF141414),
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(color: const Color(0xFF262626)),
                  gradient: const LinearGradient(
                    colors: [Color(0xFF1B1B1B), Color(0xFF111111)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 58,
                      height: 58,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: const Color(0xFFF5A623), width: 1.5),
                        color: const Color(0xFFF5A623).withValues(alpha: 0.15),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        userName.isNotEmpty ? userName[0].toUpperCase() : 'U',
                        style: const TextStyle(
                          color: Color(0xFFF5A623),
                          fontSize: 24,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  userName,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 6),
                              const Icon(Icons.verified, color: Color(0xFF4CAF50), size: 16),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              const Icon(Icons.location_on, color: Color(0xFFF5A623), size: 12),
                              const SizedBox(width: 4),
                              Text(
                                _selectedLocation,
                                style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w500),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Verified Diner • Private Profile',
                            style: TextStyle(color: Color(0xFFBA68C8), fontSize: 11, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // 2. Metrics Stat Bar
              Row(
                children: [
                  _buildProfileMetricCard(
                    'Active Bookings',
                    '${_bookedList.length}',
                    Icons.confirmation_number_outlined,
                    const Color(0xFFF5A623),
                  ),
                  const SizedBox(width: 10),
                  _buildProfileMetricCard(
                    'Attended Dinners',
                    '${_attendedList.length}',
                    Icons.dinner_dining,
                    const Color(0xFFBA68C8),
                  ),
                  const SizedBox(width: 10),
                  _buildProfileMetricCard(
                    'Notifications',
                    _notificationsAllowed ? 'Active ✓' : 'Mandatory ⚠️',
                    Icons.notifications_active,
                    _notificationsAllowed ? const Color(0xFF4CAF50) : const Color(0xFFE57373),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // 3. Vibe DNA Archetype Showcase Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: const Color(0xFF141414),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFFBA68C8).withValues(alpha: 0.35)),
                  gradient: const LinearGradient(
                    colors: [Color(0xFF22132A), Color(0xFF141414)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.auto_awesome, color: Color(0xFFBA68C8), size: 16),
                            SizedBox(width: 6),
                            Text(
                              'VIBE DNA PERSONA',
                              style: TextStyle(
                                color: Color(0xFFBA68C8),
                                fontSize: 11,
                                fontWeight: FontWeight.w900,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: const Color(0xFFBA68C8).withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Text(
                            'Curated Match',
                            style: TextStyle(color: Color(0xFFBA68C8), fontSize: 10, fontWeight: FontWeight.w800),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'The Charismatic Spark (Stark)',
                      style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Quick-witted, infectious energy, and effortlessly turns awkward silences into inside jokes and real connections.',
                      style: TextStyle(color: Colors.white70, fontSize: 12, height: 1.35),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ===============================================================
              // SECTION: PERSONALITY & MATCHMAKING
              // ===============================================================
              const Text(
                'Personality & Matchmaking',
                style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w800, letterSpacing: 0.3),
              ),
              const SizedBox(height: 10),

              // Retake Vibe DNA Test (Matches the exact pattern of the other lines!)
              _buildMenuTile(
                icon: Icons.psychology_outlined,
                title: 'Retake Vibe DNA Test',
                subtitle: 'Recalculate your conversational persona & table matches',
                color: const Color(0xFFBA68C8),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const OnboardingQuizScreen()),
                  ).then((_) => _loadProfileData());
                },
              ),

              const SizedBox(height: 16),

              // ===============================================================
              // SECTION: DINING & ACTIVITY
              // ===============================================================
              const Text(
                'Dining & Experiences',
                style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w800, letterSpacing: 0.3),
              ),
              const SizedBox(height: 10),

              // My Bookings Tile
              _buildMenuTile(
                icon: Icons.confirmation_number_outlined,
                title: 'My Bookings',
                subtitle: '${_bookedList.length} Active booked • ${_attendedList.length} Attended meetups',
                color: const Color(0xFFF5A623),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const MyBookingsScreen()),
                  ).then((_) => _loadProfileData());
                },
              ),

              // Uploaded Videos Tile
              _buildMenuTile(
                icon: Icons.video_collection_outlined,
                title: 'Uploaded Videos & Reels',
                subtitle: 'Your dinner highlights & community reels',
                color: const Color(0xFFF5A623),
                onTap: _showUploadedVideosModal,
              ),

              const SizedBox(height: 16),

              // ===============================================================
              // SECTION: APP SETTINGS & SAFETY
              // ===============================================================
              const Text(
                'Settings & Preferences',
                style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w800, letterSpacing: 0.3),
              ),
              const SizedBox(height: 10),

              // Push Notification Permissions (Mandatory)
              _buildMenuTile(
                icon: Icons.notifications_active_outlined,
                title: 'Push Notifications',
                subtitle: _notificationsAllowed
                    ? 'Mandatory for dinner reveals • Enabled ✓'
                    : '⚠️ Mandatory: Tap to allow notifications',
                color: _notificationsAllowed ? const Color(0xFF4CAF50) : const Color(0xFFF5A623),
                onTap: () {
                  _showMandatoryNotificationModal();
                },
              ),

              // How It Works Tile
              _buildMenuTile(
                icon: Icons.auto_stories_outlined,
                title: 'How It Works',
                subtitle: 'Matchmaking, progressive reveal & meetups',
                color: const Color(0xFFBA68C8),
                onTap: _showHowItWorksModal,
              ),

              // Privacy Policy Tile
              _buildMenuTile(
                icon: Icons.privacy_tip_outlined,
                title: 'Privacy Policy',
                subtitle: 'Data protection & attendee confidentiality',
                color: Colors.greenAccent,
                onTap: _showPrivacyPolicyModal,
              ),

              // Help Center Tile
              _buildMenuTile(
                icon: Icons.support_agent_outlined,
                title: 'Help Center',
                subtitle: 'Dinner etiquette, FAQs & customer support',
                color: Colors.orangeAccent,
                onTap: _showHelpCenterModal,
              ),

              // Delete Account Tile
              _buildMenuTile(
                icon: Icons.delete_forever_outlined,
                title: 'Delete Account',
                subtitle: 'Erase all personal profile data & bookings',
                color: Colors.redAccent,
                onTap: _showDeleteAccountDialog,
              ),

              const SizedBox(height: 24),

              // Sign Out Button
              SizedBox(
                width: double.infinity,
                height: 50,
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.logout, size: 18),
                  onPressed: () async {
                    final prefs = await SharedPreferences.getInstance();
                    await prefs.setBool('is_logged_out', true);
                    ApiService.instance.token = null;
                    ApiService.instance.currentUserId = null;
                    ApiService.instance.currentUserName = null;
                    if (!mounted) return;
                    Navigator.pushAndRemoveUntil(
                      context,
                      MaterialPageRoute(builder: (_) => const WelcomeScreen()),
                      (route) => false,
                    );
                  },
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.redAccent,
                    side: const BorderSide(color: Colors.redAccent, width: 1.2),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  label: const Text('Sign Out of Kalisi', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14)),
                ),
              ),
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileMetricCard(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF141414),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF222222)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(height: 6),
            Text(
              value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: color,
                fontSize: 13,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Colors.white54,
                fontSize: 10,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Settings Menu Tile Builder
  Widget _buildMenuTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF141414),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF222222)),
      ),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.15),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 20),
        ),
        title: Text(
          title,
          style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700),
        ),
        subtitle: Text(
          subtitle,
          style: const TextStyle(color: Colors.white54, fontSize: 12),
        ),
        trailing: const Icon(Icons.arrow_forward_ios, color: Colors.white24, size: 14),
      ),
    );
  }

  // ===========================================================================
  // MODALS & DIALOGS
  // ===========================================================================

  // 1. Uploaded Videos Modal & Upload Dialog
  void _showUploadedVideosModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF161616),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)),
                  ),
                ),
                const SizedBox(height: 18),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Your Dinner Videos',
                      style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900),
                    ),
                    ElevatedButton.icon(
                      icon: const Icon(Icons.add, size: 16),
                      onPressed: () {
                        Navigator.pop(ctx);
                        _showUploadVideoDialog();
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF5A623),
                        foregroundColor: Colors.black,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      ),
                      label: const Text('Upload Reel', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12)),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                if (_uploadedVideos.isEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(vertical: 30),
                    alignment: Alignment.center,
                    child: const Column(
                      children: [
                        Icon(Icons.movie_creation_outlined, color: Colors.white24, size: 48),
                        SizedBox(height: 12),
                        Text('No uploaded dinner videos yet', style: TextStyle(color: Colors.white60, fontSize: 14)),
                        SizedBox(height: 4),
                        Text(
                          'Share a video from your recent Kalisi meetup table!',
                          style: TextStyle(color: Colors.white38, fontSize: 12),
                        ),
                      ],
                    ),
                  )
                else
                  ..._uploadedVideos.map((v) {
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF222222),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Row(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: Image.network(
                              v['thumbnail_url'] ?? 'https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80',
                              width: 60,
                              height: 60,
                              fit: BoxFit.cover,
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  v['title'] ?? 'Kalisi Table Memory',
                                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 14),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  v['venue'] ?? 'Bangalore Meetup',
                                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.check_circle, color: Colors.greenAccent, size: 18),
                        ],
                      ),
                    );
                  }),
                const SizedBox(height: 16),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showUploadVideoDialog() {
    final titleCtrl = TextEditingController();
    final venueCtrl = TextEditingController(text: _selectedLocation);
    final urlCtrl = TextEditingController(text: 'https://www.w3schools.com/html/mov_bbb.mp4');
    bool isUploading = false;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (dialogCtx, setDialogState) {
            return AlertDialog(
              backgroundColor: const Color(0xFF181818),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
              title: const Text('Upload Meetup Reel', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: titleCtrl,
                      style: const TextStyle(color: Colors.white),
                      decoration: const InputDecoration(
                        labelText: 'Title / Caption',
                        labelStyle: TextStyle(color: Colors.white60),
                        hintText: 'e.g. 5 Strangers playing trivia!',
                        hintStyle: TextStyle(color: Colors.white24),
                        enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: venueCtrl,
                      style: const TextStyle(color: Colors.white),
                      decoration: const InputDecoration(
                        labelText: 'Venue / Neighborhood',
                        labelStyle: TextStyle(color: Colors.white60),
                        enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: urlCtrl,
                      style: const TextStyle(color: Colors.white),
                      decoration: const InputDecoration(
                        labelText: 'Video URL (MP4 / WebM)',
                        labelStyle: TextStyle(color: Colors.white60),
                        enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel', style: TextStyle(color: Colors.white60)),
                ),
                ElevatedButton(
                  onPressed: isUploading
                      ? null
                      : () async {
                          if (titleCtrl.text.trim().isEmpty) return;
                          setDialogState(() => isUploading = true);
                          try {
                            await ApiService.instance.uploadVideo(
                              title: titleCtrl.text.trim(),
                              venueName: venueCtrl.text.trim(),
                              videoUrl: urlCtrl.text.trim(),
                            );
                            if (!ctx.mounted) return;
                            Navigator.pop(ctx);
                            _loadProfileData();
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Video reel uploaded to Kalisi community!'),
                                  backgroundColor: Color(0xFFF5A623),
                                ),
                              );
                            }
                          } catch (e) {
                            setDialogState(() => isUploading = false);
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text(e.toString())),
                              );
                            }
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFF5A623),
                    foregroundColor: Colors.black,
                  ),
                  child: isUploading
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Publish Reel', style: TextStyle(fontWeight: FontWeight.w800)),
                ),
              ],
            );
          },
        );
      },
    );
  }

  // 3. Privacy Policy Modal
  void _showPrivacyPolicyModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF161616),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)),
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Row(
                    children: [
                      Icon(Icons.privacy_tip_outlined, color: Colors.greenAccent, size: 24),
                      SizedBox(width: 10),
                      Text('Kalisi Privacy Policy', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _buildPolicySection('1. Phone Number Secrecy', 'Your mobile number is solely used for 1-time OTP verification. It is NEVER shared with other diners, restaurant partners, or external marketing parties.'),
                  _buildPolicySection('2. Table Anonymity', 'Strangers see only your first name and your Vibe DNA conversational style. No last names, contact details, or work locations are ever disclosed.'),
                  _buildPolicySection('3. Progressive Reveal Security', 'The exact venue address and table number are held in progressive escrow until the morning of your event to prevent unverified drop-ins.'),
                  _buildPolicySection('4. Right to Deletion', 'You retain complete ownership of your data and can permanently erase your profile, bookings, and Vibe DNA quiz responses at any time.'),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildPolicySection(String heading, String body) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(heading, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(body, style: const TextStyle(color: Colors.white60, fontSize: 13, height: 1.3)),
        ],
      ),
    );
  }

  // 4. Help Center Modal
  void _showHelpCenterModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF161616),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)),
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Row(
                    children: [
                      Icon(Icons.help_outline, color: Colors.orangeAccent, size: 24),
                      SizedBox(width: 10),
                      Text('Kalisi Help Center', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _buildPolicySection('What if I am running late?', 'Please arrive within 15 minutes of the dinner start time. The table order commences promptly so everyone enjoys hot food together.'),
                  _buildPolicySection('How is food paid for?', 'Your Kalisi booking secures your seat reservation and table matchmaking. At the end of the meal, the food bill is split equally among diners at the table.'),
                  _buildPolicySection('Need support or have a feedback?', 'Reach out to our diner concierge anytime at support@kalisi.app or WhatsApp +91 98800 12345. We reply within 30 minutes!'),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  // 5. Delete Account Dialog
  void _showDeleteAccountDialog() {
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: const Color(0xFF181818),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 26),
              SizedBox(width: 10),
              Text('Delete Account?', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
            ],
          ),
          content: const Text(
            'Are you sure you want to permanently delete your Kalisi account? All your bookings, Vibe DNA profile, and meetup history will be immediately deleted.',
            style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Keep Account', style: TextStyle(color: Colors.white60)),
            ),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  await ApiService.instance.deleteAccount();
                  if (!mounted) return;
                  Navigator.pushAndRemoveUntil(
                    context,
                    MaterialPageRoute(builder: (_) => const WelcomeScreen()),
                    (route) => false,
                  );
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed to delete account: $e')),
                  );
                }
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
              child: const Text('Delete Permanently', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
            ),
          ],
        );
      },
    );
  }
}

class _MandatoryFeatureRow extends StatelessWidget {
  final IconData icon;
  final String text;

  const _MandatoryFeatureRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFFF5A623), size: 14),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w600),
          ),
        ),
      ],
    );
  }
}
