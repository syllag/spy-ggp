#include "fake_player.hpp"

unsigned int fake_player::nb_created_instances = -1;

fake_player::fake_player() {
    ++nb_created_instances;

    std::cout << "[fake_player] Constructor called" << std::endl;

    nb_steps = 0;
}

fake_player::~fake_player() {
    std::cout << "[fake_player] ☠ ☠ ☠ ☠ ☠ ☠ ☠ destructor called ☠ ☠ ☠ ☠ ☠ ☠ ☠" << std::endl;
}


float fake_player::play(std::string &s) {
  std::this_thread::sleep_for(std::chrono::milliseconds(choice_time_in_millis));

  if (nb_created_instances == 1) {
    s = "move";
  } else if  (nb_created_instances == 2 && nb_steps == 0) {
    s = "move1";
  } else if (nb_created_instances == 2 && nb_steps == 1) {
    s = "move2";
  } else {
    s = "noop";
  }


  return 0;
}



extern "C" {
  /** instance globale du joueur **/
  fake_player fp;

  int init_player() {
    std::cout << "[fake_player] init_player (): OK" << std::endl;

    return 0;
  }

  int init_game(const char *role, const char *game_description, int parsing_time_in_millis, int choice_time_in_millis) {
    fp = fake_player();

    std::cout << "[fake_player] init_game (...) " << std::endl;
    std::cout << "[fake_player] role: " << role << std::endl;
    std::cout << "[fake_player] GDL: \n" << game_description;
    std::cout << "[fake_player] parsing_time_in_millis: " << parsing_time_in_millis << std::endl;
    std::cout << "[fake_player] choice_time_in_millis: " << choice_time_in_millis << std::endl;

    fp.parsing_time_in_millis = parsing_time_in_millis;
    fp.choice_time_in_millis = choice_time_in_millis;

    std::this_thread::sleep_for(std::chrono::milliseconds(fp.parsing_time_in_millis));

    return 0;
  }

  int update(const char *chosen_actions[], size_t nb_players) {
    std::cout << "[fake_player] update (...)" << std::endl;
    std::cout << "[fake_player] nb_players: " << nb_players << std::endl;

    for (unsigned int i = 0; i < nb_players; ++i) {
      std::cout << "[fake_player] chosen_actions[" << i << "]: " << chosen_actions[i] << std::endl;
    }

    return 0;
  }


  int update2(const char *choosen_action, char *percepts[], size_t nb_percepts, int round) {
    std::cout << "[fake_player] update2 (...)" << std::endl;
    std::cout << "[fake_player] choosen_action: " << choosen_action << std::endl;

    for (unsigned int i = 0; i < nb_percepts; ++i) {
      std::cout << "[fake_player] percepts[" << i << "]: " << percepts[i] << std::endl;
    }

    return 0;
  }


  int play(char *play_buffer, size_t buffer_max_size) {
    std::string s;
    fp.play(s);

    strncpy(play_buffer, s.c_str(), buffer_max_size);

    std::cout << "[fake_player] play (...): " << play_buffer << std::endl;

    ++fp.nb_steps;

    return 0;
  }

  int end_of_game2(const char *choosen_action, char *percepts[], size_t nb_percepts, int round) {
    std::cout << "[fake_player] end_of_game2 (...)" << std::endl;
    std::cout << "[fake_player] choosen_action: " << choosen_action << std::endl;

    for (unsigned int i = 0; i < nb_percepts; ++i) {
      std::cout << "[fake_player] percepts[" << i << "]: " << percepts[i] << std::endl;
    }

    return 0;
  }


  int end_of_game(const char *chosen_actions[], size_t nb_players) {
    std::string s;

    std::cout << "[fake_player] end_of_game (...)" << std::endl;
    std::cout << "[fake_player] nb_players: " << nb_players << std::endl;

    for (unsigned int i = 0; i < nb_players; ++i) {
      std::cout << "[fake_player] chosen_actions[" << i << "]: " << chosen_actions[i] << std::endl;
    }

    ++fp.nb_steps;

    return 0;
  }


  int reset() {
    std::cout << "[fake_player] reset (): nothing to do..." << std::endl;

    return 0;
  }

}
