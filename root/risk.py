from typing import Dict, List, Tuple
import re


class RiskAssessor:
    """Assesses command risk levels for cautious/turbo modes."""
    
    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r'\brm\s+(-rf|--recursive|-f)\s',  # rm -rf
        r'\bdd\s+if=.*of=.*\b',  # dd commands
        r'\bmkfs\.',  # filesystem formatting
        r'\bformat\s',  # Windows format
        r'\bdiskutil\s',  # macOS disk utility
        r'\bchmod\s+777\b',  # chmod 777
        r'\bchown\s+.*:.*\s+/',  # chown on system paths
        r'\bsudo\s+rm\b',  # sudo rm
        r'\bsudo\s+dd\b',  # sudo dd
        r'\bkill\s+-9\b.*\d+',  # kill -9 with PID
        r'\bpkill\s+-9\b',  # pkill -9
        r'\bsudo\s+kill\b',  # sudo kill
        r'\breboot\b',  # reboot
        r'\bshutdown\b',  # shutdown
        r'\bhalt\b',  # halt
        r'\bpoweroff\b',  # poweroff
        r'\bsystemctl\s+(stop|restart|disable)\b',  # systemd service control
        r'\bservice\s+.*\s+stop\b',  # service stop
        r'\biptables\s+-F\b',  # iptables flush
        r'\bufw\s+(disable|reset)\b',  # ufw disable/reset
        r'\b:(){ :|:& };:',  # fork bomb
        r'\bsudo\s+su\b',  # sudo su
        r'\bsu\s+-\s',  # su -
        r'\bpasswd\b',  # passwd
        r'\buserdel\b',  # userdel
        r'\bgroupdel\b',  # groupdel
        r'\bcryptsetup\s+(luksErase|luksFormat)\b',  # LUKS operations
        r'\bshred\b',  # shred
        r'\bsrm\b',  # secure rm
    ]
    
    # Moderate risk patterns
    MODERATE_PATTERNS = [
        r'\brm\s',  # any rm command
        r'\bsudo\s',  # any sudo command
        r'\bchmod\s',  # any chmod
        r'\bchown\s',  # any chown
        r'\bmv\s+.*\s+/',  # move to system directories
        r'\bcp\s+.*\s+/',  # copy to system directories
        r'\bkill\b',  # kill commands
        r'\bpkill\b',  # pkill commands
        r'\bgit\s+(reset|clean|drop)\b',  # destructive git commands
        r'\bdocker\s+(rmi|rm|stop|kill)\b',  # destructive docker commands
        r'\bkubectl\s+(delete|drain)\b',  # destructive kubectl commands
        r'\bpip\s+uninstall\b',  # pip uninstall
        r'\bnpm\s+uninstall\b',  # npm uninstall
        r'\bbrew\s+uninstall\b',  # brew uninstall
        r'\bapt-get\s+(remove|purge)\b',  # apt package removal
        r'\byum\s+(remove|erase)\b',  # yum package removal
        r'\bsystemctl\s+(start|enable|mask)\b',  # systemd service changes
        r'\bservice\s+.*\s+(start|restart)\b',  # service changes
        r'\bcrontab\s+-r\b',  # crontab remove
        r'\bat\s+.*\s+rm\b',  # at with rm
        r'\bcron\b',  # cron modifications
    ]
    
    # Safe command patterns (common, low-risk operations)
    SAFE_PATTERNS = [
        r'\bls\b',
        r'\bcat\b',
        r'\bgrep\b',
        r'\bfind\b',
        r'\blocate\b',
        r'\bwhich\b',
        r'\bwhereis\b',
        r'\bfile\b',
        r'\bhead\b',
        r'\btail\b',
        r'\bwc\b',
        r'\bdate\b',
        r'\bwho\b',
        r'\bwhoami\b',
        r'\bid\b',
        r'\bpwd\b',
        r'\buname\b',
        r'\bdf\b',
        r'\bdu\b',
        r'\bfree\b',
        r'\btop\b',
        r'\bps\b',
        r'\bhistory\b',
        r'\becho\b',
        r'\bprintenv\b',
        r'\benv\b',
        r'\bcurl\b.*\s+(GET|HEAD)\b',  # read-only curl
        r'\bwget\b.*\s--spider\b',  # wget spider
        r'\bgit\s+(status|log|show|diff|branch|tag)\b',  # read-only git
        r'\bdocker\s+(ps|images|logs|inspect)\b',  # read-only docker
        r'\bkubectl\s+(get|describe|logs)\b',  # read-only kubectl
    ]
    
    def __init__(self):
        self.dangerous_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
        self.moderate_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.MODERATE_PATTERNS]
        self.safe_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.SAFE_PATTERNS]
    
    def assess_risk(self, command: str) -> Tuple[str, str]:
        """
        Assess the risk level of a command.
        
        Returns:
            Tuple of (risk_level, reason)
            risk_level: 'safe', 'moderate', or 'dangerous'
            reason: description of why the command was classified this way
        """
        command_lower = command.lower().strip()
        
        # Check for dangerous patterns first
        for regex in self.dangerous_regex:
            if regex.search(command):
                return 'dangerous', self._get_danger_reason(command)
        
        # Check for moderate patterns
        for regex in self.moderate_regex:
            if regex.search(command):
                return 'moderate', self._get_moderate_reason(command)
        
        # Check if it matches safe patterns
        for regex in self.safe_regex:
            if regex.search(command):
                return 'safe', 'Common read-only command'
        
        # Default to moderate for unknown commands
        return 'moderate', 'Unknown command pattern - treated as moderate risk'
    
    def _get_danger_reason(self, command: str) -> str:
        """Get a specific reason for dangerous classification."""
        cmd_lower = command.lower()
        
        if 'rm -rf' in cmd_lower or 'rm -fr' in cmd_lower:
            return 'Force recursive deletion - high data loss risk'
        elif 'dd if=' in cmd_lower and 'of=' in cmd_lower:
            return 'Direct disk write - potential data corruption'
        elif 'mkfs' in cmd_lower:
            return 'Filesystem formatting - complete data loss'
        elif 'format' in cmd_lower:
            return 'Disk formatting - complete data loss'
        elif 'chmod 777' in cmd_lower:
            return 'Setting world-writable permissions - security risk'
        elif 'reboot' in cmd_lower or 'shutdown' in cmd_lower:
            return 'System shutdown/restart - service interruption'
        elif 'kill -9' in cmd_lower or 'pkill -9' in cmd_lower:
            return 'Force kill process - potential data loss'
        elif 'sudo' in cmd_lower:
            return 'Privileged execution - system-wide impact'
        else:
            return 'System modification command - high impact'
    
    def _get_moderate_reason(self, command: str) -> str:
        """Get a specific reason for moderate classification."""
        cmd_lower = command.lower()
        
        if 'rm ' in cmd_lower:
            return 'File deletion - potential data loss'
        elif 'sudo' in cmd_lower:
            return 'Privileged execution - elevated permissions required'
        elif 'chmod' in cmd_lower:
            return 'Permission modification - access control changes'
        elif 'chown' in cmd_lower:
            return 'Ownership change - permission impact'
        elif 'git reset' in cmd_lower or 'git clean' in cmd_lower:
            return 'Git history modification - potential data loss'
        elif 'docker' in cmd_lower and ('rm' in cmd_lower or 'stop' in cmd_lower):
            return 'Container management - service impact'
        elif 'uninstall' in cmd_lower:
            return 'Package removal - functionality loss'
        else:
            return 'System modification - moderate impact'
    
    def should_auto_run(self, command: str, mode: str, config: Dict) -> bool:
        """
        Determine if a command should be auto-run based on mode and config.
        
        Args:
            command: The command to check
            mode: Current mode ('cautious' or 'turbo')
            config: Configuration dictionary
            
        Returns:
            True if command should be auto-run, False otherwise
        """
        risk_level, _ = self.assess_risk(command)
        
        # Turbo mode auto-runs everything
        if mode == 'turbo':
            return True
        
        # Cautious mode respects auto-trust settings
        if mode == 'cautious':
            if risk_level == 'safe' and config.get('behavior', {}).get('auto_trust_safe_commands', True):
                return True
            elif risk_level == 'moderate' and config.get('behavior', {}).get('auto_trust_moderate_commands', False):
                return True
            elif risk_level == 'dangerous':
                return False  # Never auto-run dangerous commands in cautious mode
        
        return False
    
    def get_risk_color(self, risk_level: str) -> str:
        """Get color code for risk level display."""
        colors = {
            'safe': 'green',
            'moderate': 'yellow', 
            'dangerous': 'red'
        }
        return colors.get(risk_level, 'yellow')
    
    def get_risk_symbol(self, risk_level: str) -> str:
        """Get symbol for risk level display."""
        symbols = {
            'safe': '✓',
            'moderate': '⚠',
            'dangerous': '⚡'
        }
        return symbols.get(risk_level, '?')


# Global risk assessor instance
_risk_assessor = None

def get_risk_assessor() -> RiskAssessor:
    """Get the global risk assessor instance."""
    global _risk_assessor
    if _risk_assessor is None:
        _risk_assessor = RiskAssessor()
    return _risk_assessor
