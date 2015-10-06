'''
if nodetype is primary :
  - Prompt for secondary IP (show default of 10.1.1.5)
  - Create DNS entries
  - Enable DNS on startup
  - Start DNS
  - Set grain
  - Restart salt minion
  - Enable salt-master on startup
  - Start salt-master
  - #Changes to rc.local will happen only on first time setup


if nodetype is secondary :

  - Prompt for primary IP (show default of 10.1.1.4)
  - Create DNS entries
  - Enable DNS on startup
  - Start DNS
  - Set grain
  - Restart salt minion
  - Enable salt-master on startup (only after testing salt failover) 
  - Start salt-master(only after testing salt failover)
  - #Changes to rc.local will happen only on first time setup
'''

import sys, socket
from integralstor_common import command, networking

def set_as_primary(primary_ip, primary_netmask):

  try:
    print
    print "Setting GRIDCell type to primary"
    print
    print "The IntegralStor 'primary' GRIDCell's IP address is currently %s"%primary_ip
    str_to_print = "Please confirm that this is correct (y/n) :"
    valid_input = False
    ok = False
    while not valid_input :
      input = raw_input(str_to_print)
      if input:
        if input.lower() in ['y','n']:
          valid_input = True
          if input.lower() == 'y':
            ok = True
  
    if not ok:
      raise Exception("Please set the IP configuration of this (primary) GRIDCell and then try again")
  
    str_to_print = 'Please enter the IP address of the Fractalio "secondary" GRIDCell : '    
    valid_input = False
    while not valid_input :
      print
      input = raw_input(str_to_print)
      if input:
        vi, err = networking.validate_ip(input):
        if err:
          raise Exception(err)
        if vi:
          valid_input = True
          secondary_ip = input
  
    str_to_print = "Please enter the IP address of the customer's DNS server: "
    external_dns = None
    valid_input = False
    while not valid_input :
      print
      input = raw_input(str_to_print)
      if input:
        vi, err = networking.validate_ip(input):
        if err:
          raise Exception(err)
        if vi:
          valid_input = True
          external_dns = input
      else:
        valid_input = True
  
    print
    print "Generating the DNS configuartion.."
    if external_dns:
      rc, err = networking.generate_default_primary_named_conf(primary_ip, primary_netmask, secondary_ip, True, external_dns, True)
    else:
      rc, err = networking.generate_default_primary_named_conf(primary_ip, primary_netmask, secondary_ip)
  
    if err:
      raise Exception(err)
    if not rc:
      raise Exception( "Error generating the DNS configuration file")
      
    rc, err = networking.set_name_servers([primary_ip, secondary_ip, external_dns])
  
    if not rc:
      raise Exception("Error generating the DNS resolve.conf file : %s"%err)
  
    print "Generating the DNS configuartion.. Done."
  
    print
    print "Starting the DNS server .."
    (r, rc), err = command.execute_with_rc('chkconfig named on')
    if err:
      raise Exception(err)
    if rc != 0:
      raise Exception("Error setting the DNS server to start on boot")
  
    (r, rc), err = command.execute_with_rc('service named restart')
    if err:
      raise Exception(err)
    if rc != 0:
      raise Exception("Error starting the DNS server")
  
    print "Starting the DNS server .. Done."
  
    print
    print "Setting salt grains.."
    try :
      with open('/etc/salt/grains', 'w') as f:
        f.write('# Generated by the IntegralStor script\n')
        f.write('roles:\n')
        f.write('  - primary\n')
        f.write('  - master\n')
        f.flush()
      f.close()
    except Exception, e:
      raise Exception("Error generating the grains file : %s"%e)
    print "Setting salt grains.. Done."
  
    print
    print "Setting hostname.."
    old_hostname = socket.gethostname()
    rc, err = networking.set_hostname('fractalio-pri', 'fractalio.lan')
    if err:
      raise Exception('Error setting hostname : %s'%err)
    print "Setting hostname.. Done."
  
    print
    print "Restarting salt master.."
    (r, rc), err = command.execute_with_rc('service salt-master start')
    if err:
      raise Exception(err)
    if rc != 0:
      raise Exception("Error starting the salt master")
    print "Restarting salt master.. Done."
  
    print
    print "Restarting salt minion.."
    (r, rc), err = command.execute_with_rc('service salt-minion restart')
    if err:
      raise Exception(err)
    if rc != 0:
      raise Exception("Error restarting the salt minion")
    print "Restarting salt minion.. Done."
  
    print
    print "Setting salt master to start on reboot.."
    (r, rc), err = command.execute_with_rc('chkconfig salt-master on')
    if err:
      raise Exception(err)
    if rc != 0:
      raise Exception("Error setting the salt master server to start on boot")
    print "Setting salt master to start on reboot.. Done."
  
  
    print
    print "Successfully set the GRIDCell type to primary."
  except Exception, e:
    print
    print 'Error setting GRIDCell type to primary : %s'%str(e)
    return False, 'Error setting GRIDCell type to primary : %s'%str(e)
  else:
    return True, None




def set_as_secondary(secondary_ip, secondary_netmask):

  print
  print "Setting GRIDCell type to secondary"
  print
  print "The IntegralStor 'secondary' GRIDCell's IP address is currently %s"%secondary_ip
  str_to_print = "Please confirm that this is correct (y/n) :"
  valid_input = False
  ok = False
  while not valid_input :
    input = raw_input(str_to_print)
    if input:
      if input.lower() in ['y','n']:
        valid_input = True
        if input.lower() == 'y':
          ok = True

  if not ok:
    print
    print "Please set the IP configuration of this (secondary) GRIDCell and then try again"
    return -1

  str_to_print = "Please enter the IP address of the Fractalio 'primary' GRIDCell : "    
  valid_input = False
  while not valid_input :
    input = raw_input(str_to_print)
    if input:
      vi, err = networking.validate_ip(input):
      if vi:
        valid_input = True
        primary_ip = input

  str_to_print = "Please enter the IP address of the customer's DNS server: "
  external_dns = None
  valid_input = False
  while not valid_input :
    print
    input = raw_input(str_to_print)
    if input:
      vi, err = networking.validate_ip(input):
      if vi:
        valid_input = True
        external_dns = input
    else:
      valid_input = True

  print
  print "Generating the DNS configuartion.."
  if external_dns:
    rc, err = networking.generate_default_secondary_named_conf(primary_ip, secondary_netmask, secondary_ip, True, external_dns, True)
  else:
    rc, err = networking.generate_default_secondary_named_conf(primary_ip, secondary_netmask, secondary_ip)

  if err:
    raise Exception(err)
  if rc != 0:
    raise Exception("Error generating the DNS configuration file")

  rc, err = networking.set_name_servers([primary_ip, secondary_ip, external_dns])

  if not rc:
    raise Exception("Error generating the DNS resolv.conf file : %s"%err)
    return -1
    
  print "Generating the DNS configuartion.. Done."

  print
  print "Starting the DNS server .."
  r, rc = command.execute_with_rc('chkconfig named on')
  if rc != 0:
    print "Error setting the DNS server to start on boot"
    return -1

  r, rc = command.execute_with_rc('service named restart')
  if rc != 0:
    print "Error starting the DNS server"
    return -1

  print "Starting the DNS server .. Done."

  print
  print "Setting salt grains.."
  try :
    with open('/etc/salt/grains', 'w') as f:
      f.write('# Generated by the IntegralStor script\n')
      f.write('roles:\n')
      f.write('  - secondary\n')
      f.write('  - master\n')
      f.flush()
    f.close()
  except Exception, e:
    print "Error generating the grains file : %s"%e
    return -1
  print "Setting salt grains.. Done."

  print
  print "Setting hostname.."
  old_hostname = socket.gethostname()
  rc, err = networking.set_hostname('fractalio-sec', 'fractalio.lan')
  if err:
    raise Exception('Error setting hostname : %s'%err)
  print "Setting hostname.. Done."

  print
  print "Restarting salt services.."
  r, rc = command.execute_with_rc('service salt-minion restart')
  if rc != 0:
    print "Error restarting the salt minion"
    return -1
  print "Restarting salt services.. Done."

  print
  print "Successfully set the GRIDCell type to primary."

  '''
  THE FOLLOWING SHOULD BE DONE ONLY AFTER TESTING SALT FAILOVER AND MAKING APPROPRIATE CHANGES!

  r, rc = command.execute_with_rc('chkconfig salt-master on')
  if rc != 0:
    print "Error setting the salt master server to start on boot"
    return -1

  r, rc = command.execute_with_rc('service salt-master start')
  if rc != 0:
    print "Error starting the salt master"
    return -1
  print "Restarting salt services.. Done."
  '''

  print
  print "Successfully changed the GRIDCell type to secondary"
  return 0
  return 0

if __name__ == '__main__':

  if len(sys.argv) < 2 :
    print "Please specify the GRIDCell type"
    sys.exit(-1)
  node_type = sys.argv[1]

  if node_type not in ["primary", "secondary"]:
    print "Please specify a valid GRIDCell type"
    sys.exit(-1)

  ip_info, err = networking.get_ip_info('bond0')
  if err:
    print "Error retrieving IP address information. No bonding configured? Incorrect configuration. Please configure networking. Error : %s"%err
    sys.exit(-1)

  if not ip_info:
    print "Error retrieving IP address information. No bonding configured? Incorrect configuration. Please configure networking."
    sys.exit(-1)

  ip = ip_info["ipaddr"]
  netmask = ip_info["netmask"]

  if node_type == 'primary':
    rc = set_as_primary(ip, netmask)
    sys.exit(rc)
  else:
    rc = set_as_secondary(ip, netmask)
    sys.exit(rc)

