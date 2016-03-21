#ifndef __FAKE_PLAYER__HPP__
#define __FAKE_PLAYER__HPP__

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <chrono>
#include <thread>

struct fake_player {
  unsigned int nb_steps;
  static unsigned int nb_created_instances;
  int parsing_time_in_millis;
  int choice_time_in_millis;

  fake_player();
  ~fake_player();
  float play(std::string &s);

};



extern "C" {
  int init_player();

  int init_game(const char *role, const char *game_description, int parsing_time_in_millis, int choice_time_in_millis);

  int update(const char *choosen_actions[], size_t nb_players);

  int play(char *play_buffer, size_t buffer_max_size);
  int end_of_game(const char *chosen_actions[], size_t nb_players);

  /* GDL2 version of update */
  int update2(const char *choosen_action, char *percepts[], size_t nb_percepts, int round);
  int end_of_game2(const char *choosen_action, char *percepts[], size_t nb_percepts, int round);

  int reset(); // NON UTILISÉE

  // TODO:
  // int get_game_property(char* property_name, char*buffer, size_t buffer_size)
  // Changement API update
}


#endif
