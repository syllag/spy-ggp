#include <iostream>
#include "fake_player.hpp"



int main() {
    init();
    reset();

    //std::cout << "nb_steps: " << fp.get_nb_steps() << std::endl;
    std::cout << "nb_created_instances: " << get_nb_created_instances() << std::endl;
}
