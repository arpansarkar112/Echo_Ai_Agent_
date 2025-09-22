-- Create the chat_sessions table
CREATE TABLE public.chat_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    title text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE public.chat_sessions OWNER TO postgres;
ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create the chat_messages table
CREATE TABLE public.chat_messages (
    id bigint NOT NULL,
    session_id uuid NOT NULL,
    role text NOT NULL,
    content text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE public.chat_messages OWNER TO postgres;
CREATE SEQUENCE public.chat_messages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.chat_messages_id_seq OWNER TO postgres;
ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;
ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);
ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;

-- Enable Row Level Security (RLS)
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Allow users to view their own chat sessions" ON public.chat_sessions FOR SELECT USING ((auth.uid() = user_id));
CREATE POLICY "Allow users to create their own chat sessions" ON public.chat_sessions FOR INSERT WITH CHECK ((auth.uid() = user_id));
CREATE POLICY "Allow users to manage messages in their own sessions" ON public.chat_messages FOR ALL USING (
    (
        (auth.uid() IN ( SELECT chat_sessions.user_id
           FROM public.chat_sessions
          WHERE (chat_sessions.id = chat_messages.session_id)))
    )
);
