import java.io.*;
import java.math.BigInteger;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) {
            StringTokenizer st = new StringTokenizer(line);
            while (st.hasMoreTokens()) {
                String s = st.nextToken();
                if (s.equals("0")) {
                    System.out.print(sb);
                    return;
                }
                BigInteger a = BigInteger.ONE;
                BigInteger b = BigInteger.ONE;
                for (int i = 1; i < s.length(); i++) {
                    BigInteger c = BigInteger.ZERO;
                    char cur = s.charAt(i);
                    char prev = s.charAt(i - 1);
                    if (cur != '0') {
                        c = c.add(b);
                    }
                    if (prev == '1' || (prev == '2' && cur <= '6')) {
                        c = c.add(a);
                    }
                    a = b;
                    b = c;
                }
                sb.append(b).append('\n');
            }
        }
        System.out.print(sb);
    }
}
