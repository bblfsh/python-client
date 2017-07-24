%module pyuast
%{
  #include <libuast/node.h>
%}

%include <stdint.i>
%include <std_string.i>
%include <std_vector.i>
%include <std_map.i>
%include <libuast/node.h>

namespace std {
   %template(NodeVector) vector<Node *>;
   %template(PropMap) map<string, string>;
}

%extend Node {
  const std::string __str__() {
    return self->as_string();
  }
};
