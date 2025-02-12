variable img_display_name {
  type = string
  default = "almalinux-9.4-20240805"
}

variable namespace {
  type = string
  default = "ucabm68-comp0235-ns"
}

variable network_name {
  type = string
  default = "ucabm68-comp0235-ns/ds4eng"
}

variable username {
  type = string
#  default = ""
}

variable keyname {
  type = string
  default = "ucabm86"
}

variable vm_count {
  type    = number
  default = 1
}
