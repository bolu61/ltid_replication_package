import java.util.logging.Logger;

public class WhileEmptyBody {
    private static Logger logger = Logger.getLogger(LogWithID.class.getName());

    public static void main(String... argv) {
        while (false) {

        }

        logger.info("sweet pineapple");
    }
}
